"""
API Gateway - Main Application Entry Point
"""
import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routes import health, users

# Initialize logger
logger = logging.getLogger(__name__)

# ==================== FastAPI App Initialization ====================

app = FastAPI(
    title="E-commerce API Gateway",
    version=settings.api_version,
    description="Single entry point for microservices",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# ==================== CORS Middleware ====================

# Get CORS origins as list from settings
cors_origins_list = settings.get_cors_origins_list()

# Security check: If using wildcard, must disable credentials
allow_credentials = True
if "*" in cors_origins_list:
    allow_credentials = False
    logger.warning(
        "CORS configured with wildcard origin. "
        "allow_credentials set to False for security."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ==================== Router Registration ====================

# Health router (no prefix - routes are /health)
app.include_router(health.router)

# Users router (already has prefix="/users" - don't add prefix again!)
app.include_router(users.router)

# ==================== Startup Event ====================


@app.on_event("startup")
async def startup_event():
    """
    Application startup event.

    Initializes ServiceClient and logs configuration.
    """
    # ServiceClient singleton auto-initializes on first use
    logger.info("API Gateway started")
    logger.info(f"Version: {settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug_mode}")
    logger.info(f"Gateway port: {settings.gateway_port}")

    logger.info("Configured services:")
    if settings.user_service_url:
        logger.info(f"  - User Service: {settings.user_service_url}")
    if settings.product_service_url:
        logger.info(f"  - Product Service: {settings.product_service_url}")
    if settings.order_service_url:
        logger.info(f"  - Order Service: {settings.order_service_url}")
    if settings.notification_service_url:
        logger.info(f"  - Notification Service: {settings.notification_service_url}")

    logger.info(f"CORS origins: {cors_origins_list}")
    logger.info(f"Request timeout: {settings.request_timeout}s")
    logger.info(f"Max retries: {settings.max_retries}")

# ==================== Shutdown Event ====================


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event.

    Closes ServiceClient HTTP connections.
    """
    from app.utils.http_client import service_client

    logger.info("API Gateway shutting down")

    # Close ServiceClient connections
    await service_client.close()

    logger.info("ServiceClient closed successfully")

# ==================== Global Exception Handler ====================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.

    Logs full traceback server-side, returns generic error client-side.
    """
    # Log full traceback with request context (server-side)
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "request_id": request.headers.get("X-Request-ID", "unknown")
        }
    )

    # Generic error message (client-side - don't leak details)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# ==================== Root Endpoint ====================


@app.get("/")
async def root():
    """
    Root endpoint - Gateway information.

    Returns:
        Gateway metadata including version, status, environment, and timestamp.
    """
    return {
        "name": "E-commerce API Gateway",
        "version": settings.api_version,
        "status": "running",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
