"""
API routes for user authentication and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse, TokenResponse

# Note: CORS is handled by API Gateway
# Note: Rate limiting is a future consideration

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    - Normalizes email to lowercase
    - Validates unique email and username
    - Hashes password securely
    - Returns user data (excludes password)
    """
    # Normalize email to lowercase
    user_data.email = user_data.email.lower()

    try:
        # Check if email or username already exists
        result = await db.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already exists"
            )

        # Hash password
        hashed_password = get_password_hash(user_data.password)

        # Create new user
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already exists"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user and return JWT token.

    - Validates credentials
    - Checks account status
    - Returns access token

    Note: Uses generic error messages for security (don't reveal which field is wrong)
    """
    # Find user by email (normalized to lowercase)
    result = await db.execute(
        select(User).where(User.email == credentials.email.lower())
    )
    user = result.scalar_one_or_none()

    # Verify user exists, has a password set, and password is correct
    if not user or not user.hashed_password or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active (use same error message for security)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return current_user
