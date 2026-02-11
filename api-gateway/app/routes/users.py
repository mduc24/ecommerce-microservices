"""
API Gateway - User Service Routes (Proxy)
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.middleware.auth import get_current_user
from app.utils.http_client import ServiceClient

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
async def register_user(request: Request):
    """
    Proxy request to User Service - Register new user.

    Public endpoint (no authentication required).

    Body (from client):
        {
            "email": "user@example.com",
            "username": "john_doe",
            "password": "SecurePass123!"
        }

    Returns:
        User object + access_token from User Service
    """
    # Get request body
    body = await request.json()

    # Create service client
    service_client = ServiceClient()

    # Forward request to User Service
    result = await service_client.forward_request(
        service_url=settings.user_service_url,
        method="POST",
        path="/api/v1/users/register",
        body=body
    )

    # Handle response
    if isinstance(result, tuple):
        # Error from ServiceClient (503, 504, etc.)
        status_code, error_dict = result
        return JSONResponse(status_code=status_code, content=error_dict)

    # Success - return httpx.Response as-is
    return JSONResponse(
        status_code=result.status_code,
        content=result.json()
    )


@router.post("/login")
async def login_user(request: Request):
    """
    Proxy request to User Service - User login.

    Public endpoint (no authentication required).

    Body (from client):
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }

    Returns:
        {
            "access_token": "eyJ...",
            "token_type": "bearer"
        }
    """
    # Get request body
    body = await request.json()

    # Create service client
    service_client = ServiceClient()

    # Forward request to User Service
    result = await service_client.forward_request(
        service_url=settings.user_service_url,
        method="POST",
        path="/api/v1/users/login",
        body=body
    )

    # Handle response
    if isinstance(result, tuple):
        # Error from ServiceClient (503, 504, etc.)
        status_code, error_dict = result
        return JSONResponse(status_code=status_code, content=error_dict)

    # Success - return httpx.Response as-is
    return JSONResponse(
        status_code=result.status_code,
        content=result.json()
    )


@router.get("/me")
async def get_user_profile(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """
    Proxy request to User Service - Get current user profile.

    Protected endpoint (requires JWT authentication).

    Headers:
        Authorization: Bearer <JWT_TOKEN>

    Returns:
        User object from User Service
    """
    # Extract Authorization header
    auth_header = request.headers.get("Authorization")

    # Build headers to forward
    headers = {}
    if auth_header:
        headers["Authorization"] = auth_header

    # Create service client
    service_client = ServiceClient()

    # Forward request to User Service
    # Note: No X-User-ID header - User Service validates JWT itself
    result = await service_client.forward_request(
        service_url=settings.user_service_url,
        method="GET",
        path="/api/v1/users/me",
        headers=headers
    )

    # Handle response
    if isinstance(result, tuple):
        # Error from ServiceClient (503, 504, etc.)
        status_code, error_dict = result
        return JSONResponse(status_code=status_code, content=error_dict)

    # Success - return httpx.Response as-is
    return JSONResponse(
        status_code=result.status_code,
        content=result.json()
    )
