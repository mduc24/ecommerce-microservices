"""
API Gateway - Google OAuth Proxy Routes

These routes require follow_redirects=False so the browser receives
the redirect (not the gateway). A dedicated httpx client is used
instead of ServiceClient for this reason.
"""
from typing import Optional

import httpx
from fastapi import APIRouter, Cookie
from fastapi.responses import JSONResponse, RedirectResponse

from app.config.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google")
async def google_login():
    """
    Proxy GET /auth/google → user-service.

    Returns the Google consent screen redirect to the browser and
    forwards the oauth_state CSRF cookie from user-service.
    """
    async with httpx.AsyncClient(follow_redirects=False) as client:
        response = await client.get(f"{settings.user_service_url}/auth/google")

    if response.status_code not in (301, 302, 307, 308):
        return JSONResponse(
            status_code=response.status_code,
            content={"error": "Unexpected response from auth service"},
        )

    location = response.headers.get("location")
    redirect_response = RedirectResponse(url=location)

    # Forward the oauth_state CSRF cookie to the browser (set on gateway domain)
    oauth_state = response.cookies.get("oauth_state")
    if oauth_state:
        redirect_response.set_cookie(
            key="oauth_state",
            value=oauth_state,
            max_age=300,
            httponly=True,
            samesite="lax",
        )

    return redirect_response


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    oauth_state: Optional[str] = Cookie(default=None),
):
    """
    Proxy GET /auth/google/callback → user-service.

    Forwards code + state query params and the oauth_state cookie
    so user-service can verify the CSRF state and complete OAuth.
    """
    async with httpx.AsyncClient(follow_redirects=False) as client:
        response = await client.get(
            f"{settings.user_service_url}/auth/google/callback",
            params={"code": code, "state": state},
            cookies={"oauth_state": oauth_state} if oauth_state else {},
        )

    if response.status_code not in (301, 302, 307, 308):
        content = {}
        try:
            content = response.json()
        except Exception:
            content = {"error": "Auth callback failed"}
        return JSONResponse(status_code=response.status_code, content=content)

    location = response.headers.get("location")
    redirect_response = RedirectResponse(url=location)
    redirect_response.delete_cookie(key="oauth_state")
    return redirect_response
