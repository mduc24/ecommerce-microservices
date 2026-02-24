"""
Notification Service - FastAPI application.

Consumes order events from AWS SQS and sends email notifications via SMTP.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.database import engine, Base
from app.events.consumer import event_consumer
from app.routes import router
from app.websocket.routes import router as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    logger.info("Starting %s...", settings.app_name)

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")

    # Start SQS consumer as background task
    consumer_task = asyncio.create_task(event_consumer.start())

    yield

    # Shutdown
    await event_consumer.stop()
    consumer_task.cancel()
    await engine.dispose()
    logger.info("%s stopped", settings.app_name)


app = FastAPI(
    title="Notification Service",
    description="Email notification microservice for e-commerce platform",
    version="0.1.0",
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
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}
