"""
RabbitMQ consumer for order events.
"""

import json
import logging

import aio_pika

from app.config.settings import settings
from app.database import AsyncSessionLocal
from app.models import Notification
from app.services.email_service import send_email

logger = logging.getLogger(__name__)


class OrderEventConsumer:
    """Consumes order events from RabbitMQ and sends email notifications."""

    def __init__(self):
        self._connection = None
        self._channel = None

    async def start(self):
        """Connect to RabbitMQ and start consuming order events."""
        try:
            self._connection = await aio_pika.connect_robust(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                login=settings.rabbitmq_user,
                password=settings.rabbitmq_pass,
            )
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=10)

            exchange = await self._channel.declare_exchange(
                settings.rabbitmq_exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            queue = await self._channel.declare_queue(
                settings.rabbitmq_queue,
                durable=True,
            )

            await queue.bind(exchange, routing_key="order.created")
            await queue.bind(exchange, routing_key="order.status.updated")

            await queue.consume(self._on_message)

            logger.info(
                "Consumer started on queue '%s', bound to: order.created, order.status.updated",
                settings.rabbitmq_queue,
            )
        except Exception as e:
            logger.error("Failed to start consumer: %s", e)
            self._connection = None
            self._channel = None

    async def _on_message(self, message: aio_pika.abc.AbstractIncomingMessage):
        """Process incoming message: save notification, send email, always ACK."""
        async with message.process():
            routing_key = message.routing_key
            try:
                body = json.loads(message.body.decode())
                data = body.get("data", {})
                logger.info("Received event: %s", routing_key)

                if routing_key == "order.created":
                    await self._handle_order_created(data)
                elif routing_key == "order.status.updated":
                    await self._handle_order_status_updated(data)
                else:
                    logger.warning("Unknown routing key: %s", routing_key)

            except Exception as e:
                logger.error("Error processing event %s: %s", routing_key, e)

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

        # Save notification as pending
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

            # Send email
            result = await send_email(
                to=user_email,
                subject=subject,
                template_name="order_confirmation.html",
                context=template_context,
            )

            # Update notification status
            notification.status = result["status"]
            notification.error_message = result.get("error_message")
            await db.commit()

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

        logger.info(
            "Status update %s for order #%s (%s -> %s) to %s",
            result["status"], order_id, old_status, new_status, user_email,
        )

    async def stop(self):
        """Close RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("Consumer connection closed")


event_consumer = OrderEventConsumer()
