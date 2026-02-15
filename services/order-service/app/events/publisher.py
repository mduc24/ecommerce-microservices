"""
Event publisher for RabbitMQ messaging.
"""

import json
import logging

import aio_pika
from pydantic import BaseModel

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes events to RabbitMQ topic exchange."""

    def __init__(self):
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self):
        """Connect to RabbitMQ and declare topic exchange."""
        try:
            self._connection = await aio_pika.connect_robust(
                host=settings.rabbitmq_host,
                port=settings.rabbitmq_port,
                login=settings.rabbitmq_user,
                password=settings.rabbitmq_pass,
            )
            self._channel = await self._connection.channel()
            self._exchange = await self._channel.declare_exchange(
                settings.rabbitmq_exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            logger.info(
                "Connected to RabbitMQ at %s:%s, exchange: %s",
                settings.rabbitmq_host,
                settings.rabbitmq_port,
                settings.rabbitmq_exchange,
            )
        except Exception as e:
            logger.error("Failed to connect to RabbitMQ: %s", e)
            self._connection = None
            self._channel = None
            self._exchange = None

    async def publish(self, event: BaseModel, routing_key: str):
        """Publish an event to the exchange with the given routing key."""
        if not self._exchange:
            logger.warning("RabbitMQ not connected. Skipping event: %s", routing_key)
            return

        try:
            message = aio_pika.Message(
                body=json.dumps(event.model_dump()).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await self._exchange.publish(message, routing_key=routing_key)
            logger.info("Published event: %s", routing_key)
        except Exception as e:
            logger.error("Failed to publish event %s: %s", routing_key, e)

    async def close(self):
        """Close RabbitMQ connection."""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("RabbitMQ connection closed")


event_publisher = EventPublisher()
