"""
Google OAuth2 endpoints.
"""

import secrets
import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.auth import create_access_token
from app.config.settings import settings
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["oauth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_REDIRECT_URI = "http://localhost:8003/auth/google/callback"


@router.get("/google")
async def google_login():
    """Redirect user to Google consent screen with CSRF state token."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(32)

    params = (
        f"client_id={settings.google_client_id}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&access_type=offline"
        f"&state={state}"
    )
    response = RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{params}")
    # Store state in short-lived cookie for CSRF verification on callback
    response.set_cookie(
        key="oauth_state",
        value=state,
        max_age=300,  # 5 minutes
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
    oauth_state: Optional[str] = Cookie(default=None),
):
    """Exchange code for token, upsert user, redirect to frontend with JWT."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    # CSRF check — state must match cookie set during /auth/google
    if not oauth_state or not secrets.compare_digest(oauth_state, state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    async with httpx.AsyncClient() as client:
        # Exchange authorization code for Google access token
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange Google token")

        google_access_token = token_response.json().get("access_token")

        # Fetch user info from Google
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch Google user info")

        google_user = userinfo_response.json()

    google_id = google_user.get("id")
    email = google_user.get("email", "").lower()
    name = google_user.get("name", "")

    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Invalid user info from Google")

    # Find existing user by google_id first, then by email
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user:
        # Link google_id if not already linked
        if not user.google_id:
            user.google_id = google_id
            await db.commit()
            await db.refresh(user)
    else:
        # Create new user (no password — OAuth only)
        username = email.split("@")[0]
        # Ensure username is unique by appending google_id suffix if needed
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            username = f"{username}_{google_id[:6]}"

        user = User(
            email=email,
            username=username,
            hashed_password=None,
            google_id=google_id,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate JWT and redirect to frontend
    jwt_token = create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(
        url=f"{settings.frontend_url}/auth/callback?token={jwt_token}"
    )
    # Clear the CSRF state cookie
    response.delete_cookie(key="oauth_state")
    return response
