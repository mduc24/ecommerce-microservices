"""
API Gateway - Main Application Entry Point
"""
import asyncio
import logging
from datetime import datetime

import websockets
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.routes import health, users, products, orders, notifications, auth

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

# Products router (prefix="/products")
app.include_router(products.router)

# Orders router (prefix="/orders")
app.include_router(orders.router)

# Notifications router (prefix="/notifications")
app.include_router(notifications.router)

# Auth router (prefix="/auth") - Google OAuth proxy
app.include_router(auth.router)

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

# ==================== WebSocket Proxy ====================


@app.websocket("/ws/notifications")
async def websocket_proxy(client_ws: WebSocket):
    """
    Proxy WebSocket connection to notification-service.

    Bidirectional forwarding between gateway client and backend service.
    """
    await client_ws.accept()

    # Build backend WebSocket URL
    backend_url = settings.notification_service_url.replace("http://", "ws://") + "/ws"

    try:
        async with websockets.connect(backend_url) as backend_ws:

            async def forward_client_to_backend():
                """Forward messages from gateway client to notification-service."""
                try:
                    while True:
                        data = await client_ws.receive_text()
                        await backend_ws.send(data)
                except WebSocketDisconnect:
                    await backend_ws.close()
                except Exception:
                    pass

            async def forward_backend_to_client():
                """Forward messages from notification-service to gateway client."""
                try:
                    async for message in backend_ws:
                        await client_ws.send_text(message)
                except Exception:
                    pass

            # Run both directions concurrently
            client_task = asyncio.create_task(forward_client_to_backend())
            backend_task = asyncio.create_task(forward_backend_to_client())

            # Wait for either direction to finish (disconnect)
            done, pending = await asyncio.wait(
                [client_task, backend_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel the other task
            for task in pending:
                task.cancel()

    except Exception as e:
        logger.error("WebSocket proxy error: %s", e)
    finally:
        try:
            await client_ws.close()
        except Exception:
            pass


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
