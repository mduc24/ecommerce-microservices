"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(
        ...,
        example="user@example.com",
        description="User email address"
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        example="johndoe",
        description="Unique username"
    )
    password: str = Field(
        ...,
        min_length=8,
        example="SecurePass123!",
        description="User password (min 8 characters)"
    )

    @field_validator('email')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower().strip()


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., example="SecurePass123!")


class UserResponse(BaseModel):
    """Schema for user response (public data only)."""

    id: int = Field(..., example=1)
    email: EmailStr = Field(..., example="user@example.com")
    username: str = Field(..., example="johndoe")
    is_active: bool = Field(..., example=True)
    created_at: datetime = Field(..., example="2024-01-01T00:00:00")
    updated_at: datetime = Field(..., example="2024-01-01T00:00:00")

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class UserInDB(UserResponse):
    """
    Internal schema with hashed password.

    Extends UserResponse and adds hashed_password.
    Used internally only, NOT for API responses.
    """

    hashed_password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(default="bearer", example="bearer")
