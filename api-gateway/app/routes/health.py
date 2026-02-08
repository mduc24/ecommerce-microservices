"""
API Gateway - Health Check Routes
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Gateway health check endpoint
    """
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0"
    }


@router.get("/health/services")
async def services_health():
    """
    Check health of all backend services
    """
    # Placeholder - will check all microservices health
    pass
