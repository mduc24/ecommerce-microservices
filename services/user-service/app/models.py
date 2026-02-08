"""
Database models for user service.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.database import Base


class User(Base):
    """User model for authentication and profile management."""

    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # User credentials
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps (UTC)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
