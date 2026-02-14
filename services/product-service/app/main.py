"""
Product Service - FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.settings import settings
from app.database import engine
from app.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # Startup: test database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.warning(f"Database connection failed on startup: {e}")

    yield

    # Shutdown: dispose engine connections
    await engine.dispose()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Product catalog microservice for e-commerce platform",
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS middleware (allow all for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint with database connectivity status.

    Returns:
        dict: Service health status including database connection
    """
    db_status = "connected"
    status = "healthy"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
        status = "unhealthy"

    return {
        "status": status,
        "service": settings.app_name,
        "version": settings.api_version,
        "database": db_status,
    }
