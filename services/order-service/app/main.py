"""
Order Service - FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config.settings import settings
from app.database import engine
from app.events.publisher import event_publisher
from app.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")
    except Exception as e:
        logger.warning(f"Database connection failed on startup: {e}")

    await event_publisher.connect()
    app.state.event_publisher = event_publisher

    yield

    await event_publisher.close()
    await engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title=settings.app_name,
    description="Order processing microservice for e-commerce platform",
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check with database connectivity status."""
    db_status = "connected"
    health = "healthy"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
        health = "unhealthy"

    return {
        "status": health,
        "service": settings.app_name,
        "version": settings.api_version,
        "database": db_status,
    }
