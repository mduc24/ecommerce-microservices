"""
API Gateway - Authentication Middleware
"""
from fastapi import Request, HTTPException
from jose import jwt, JWTError, ExpiredSignatureError
from app.config.settings import settings


def verify_jwt_token(token: str) -> str:
    """
    Verify JWT token and extract user_id.

    Args:
        token: JWT token string

    Returns:
        str: user_id from "sub" claim

    Raises:
        HTTPException: 401 with specific error
    """
    try:
        # Decode JWT with secret key and algorithm
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        # Validate "sub" claim exists
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Return user_id as string
        return user_id

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(request: Request) -> str:
    """
    FastAPI dependency to extract authenticated user_id.

    Usage:
        @router.get("/me")
        async def get_me(user_id: str = Depends(get_current_user)):
            ...
    """
    # Extract Authorization header
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Validate "Bearer " prefix
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token
    token = auth_header.replace("Bearer ", "", 1)

    # Verify token and get user_id
    user_id = verify_jwt_token(token)

    # Store in request.state for logging
    request.state.user_id = user_id

    return user_id
