"""
Database configuration and session management.

Connection pool settings are optimized for dev/staging environments.
Production deployments may require adjustments based on load.
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)
from sqlalchemy.orm import declarative_base

from app.config.settings import settings

# Create async engine with connection pool configuration
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    echo_pool=settings.debug,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI
async def get_db() -> AsyncSession:
    """
    Async database session dependency.

    Yields:
        AsyncSession: Database session

    Note:
        Routes must handle their own commit/rollback logic.
        This dependency only provides the session and handles cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
