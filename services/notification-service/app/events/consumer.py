"""
SQS consumer for order events.
"""

import asyncio
import json
import logging
from datetime import datetime

import aioboto3

from app.config.settings import settings
from app.database import AsyncSessionLocal
from app.models import Notification
from app.services.email_service import send_email
from app.websocket.manager import manager

logger = logging.getLogger(__name__)


class OrderEventConsumer:
    """Consumes order events from AWS SQS queue via long polling."""

    def __init__(self):
        self._session = aioboto3.Session()
        self._queue_url: str | None = None
        self._running = False

    def _client(self):
        """Return SQS async client context manager."""
        kwargs = {
            "region_name": settings.aws_region,
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }
        if settings.aws_endpoint_url:
            kwargs["endpoint_url"] = settings.aws_endpoint_url
        return self._session.client("sqs", **kwargs)

    async def initialize(self):
        """Resolve SQS queue URL from queue name."""
        try:
            async with self._client() as client:
                response = await client.get_queue_url(QueueName=settings.sqs_queue_name)
                self._queue_url = response["QueueUrl"]
            logger.info("SQS queue initialized: %s", self._queue_url)
        except Exception as e:
            logger.error("Failed to initialize SQS consumer: %s", e)
            self._queue_url = None

    async def start(self):
        """Initialize and run the SQS polling loop."""
        await self.initialize()
        if not self._queue_url:
            logger.error("SQS queue not available. Consumer not started.")
            return

        self._running = True
        logger.info("SQS consumer polling started on: %s", self._queue_url)

        while self._running:
            try:
                await self._poll()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Polling error: %s. Retrying in 5s...", e)
                await asyncio.sleep(5)

        logger.info("SQS consumer polling stopped")

    async def _poll(self):
        """Single long-poll cycle: receive up to 10 messages and process each."""
        async with self._client() as client:
            response = await client.receive_message(
                QueueUrl=self._queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                MessageAttributeNames=["All"],
            )

        messages = response.get("Messages", [])
        for message in messages:
            await self._process_message(message)

    async def _process_message(self, message: dict):
        """Parse SNS envelope, route by event_type, delete only on success."""
        receipt_handle = message["ReceiptHandle"]
        try:
            # SNS wraps messages: {"Type": "Notification", "Subject": "...", "Message": "{...}"}
            envelope = json.loads(message["Body"])
            event_type = envelope.get("Subject", "")
            inner = json.loads(envelope["Message"])
            data = inner.get("data", {})

            logger.info("Received event: %s", event_type)

            if event_type == "order.created":
                await self._handle_order_created(data)
            elif event_type == "order.status.updated":
                await self._handle_order_status_updated(data)
            else:
                logger.warning("Unknown event type: %s — skipping", event_type)

            # Delete message only after successful processing
            async with self._client() as client:
                await client.delete_message(
                    QueueUrl=self._queue_url,
                    ReceiptHandle=receipt_handle,
                )
            logger.info("Message deleted after processing: %s", event_type)

        except Exception as e:
            # Leave in queue — SQS will redeliver after visibility timeout
            logger.error("Failed to process message, leaving in queue for retry: %s", e)

    async def _handle_order_created(self, data: dict):
        """Handle order.created event: send confirmation email."""
        order_id = data["order_id"]
        user_id = data["user_id"]
        user_email = data.get("user_email", f"user_{user_id}@example.com")

        subject = f"Order #{order_id} Confirmed"
        template_context = {
            "user_email": user_email,
            "order_id": order_id,
            "total_amount": data["total_amount"],
            "items": data.get("items", []),
            "status": data.get("status", "pending"),
        }

        async with AsyncSessionLocal() as db:
            notification = Notification(
                type="order_confirmation",
                recipient_email=user_email,
                subject=subject,
                body="",
                order_id=order_id,
                user_id=user_id,
                status="pending",
            )
            db.add(notification)
            await db.commit()
            await db.refresh(notification)

            result = await send_email(
                to=user_email,
                subject=subject,
                template_name="order_confirmation.html",
                context=template_context,
            )

            notification.status = result["status"]
            notification.error_message = result.get("error_message")
            await db.commit()

        if result["status"] == "sent":
            await manager.broadcast({
                "type": "notification",
                "data": {
                    "event_type": "order_confirmation",
                    "subject": subject,
                    "message": f"Order #{order_id} confirmed",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            })

        logger.info(
            "Order confirmation %s for order #%s to %s",
            result["status"], order_id, user_email,
        )

    async def _handle_order_status_updated(self, data: dict):
        """Handle order.status.updated event: send status update email."""
        order_id = data["order_id"]
        old_status = data["old_status"]
        new_status = data["new_status"]
        user_id = data.get("user_id", 0)
        user_email = data.get("user_email", f"user_{user_id}@example.com")

        subject = f"Order #{order_id} Status: {new_status.title()}"
        template_context = {
            "user_email": user_email,
            "order_id": order_id,
            "old_status": old_status,
            "new_status": new_status,
        }

        async with AsyncSessionLocal() as db:
            notification = Notification(
                type="order_status_update",
                recipient_email=user_email,
                subject=subject,
                body="",
                order_id=order_id,
                user_id=user_id,
                status="pending",
            )
            db.add(notification)
            await db.commit()
            await db.refresh(notification)

            result = await send_email(
                to=user_email,
                subject=subject,
                template_name="order_status_update.html",
                context=template_context,
            )

            notification.status = result["status"]
            notification.error_message = result.get("error_message")
            await db.commit()

        if result["status"] == "sent":
            await manager.broadcast({
                "type": "notification",
                "data": {
                    "event_type": "order_status_update",
                    "subject": subject,
                    "message": f"Order #{order_id}: {old_status} → {new_status}",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            })

        logger.info(
            "Status update %s for order #%s (%s -> %s) to %s",
            result["status"], order_id, old_status, new_status, user_email,
        )

    async def stop(self):
        """Signal the polling loop to stop."""
        self._running = False
        logger.info("SQS consumer stop requested")


event_consumer = OrderEventConsumer()
