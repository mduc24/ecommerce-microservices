"""
API Gateway - User Service Routes
"""
from fastapi import APIRouter, Depends
from app.config.settings import settings

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/register")
async def register_user():
    """
    Proxy request to User Service - Register new user
    """
    # Placeholder - will proxy to user-service
    pass


@router.post("/login")
async def login_user():
    """
    Proxy request to User Service - User login
    """
    # Placeholder - will proxy to user-service
    pass


@router.get("/me")
async def get_current_user():
    """
    Proxy request to User Service - Get current user info
    """
    # Placeholder - will proxy to user-service with JWT
    pass
