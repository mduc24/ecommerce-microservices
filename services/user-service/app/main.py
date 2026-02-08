"""
User Service - FastAPI application entry point.
"""

from fastapi import FastAPI

from app.config.settings import settings
from app.routes import router

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="User management microservice for e-commerce platform",
    version="0.1.0",
    debug=settings.debug,
)

# Include routers
app.include_router(router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Service health status
    """
    return {
        "status": "healthy",
        "service": settings.app_name
    }
