"""
Test consumer for order service events.

Usage:
    docker-compose exec order-service python -m app.events.consumer
"""

import asyncio
import json
import logging

import aio_pika

from app.config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def on_message(message: aio_pika.abc.AbstractIncomingMessage):
    """Handle incoming message from RabbitMQ."""
    async with message.process():
        routing_key = message.routing_key
        body = json.loads(message.body.decode())

        logger.info("Received event: %s", routing_key)
        logger.info("Payload: %s", json.dumps(body, indent=2))
        logger.info("-" * 60)


async def main():
    """Connect to RabbitMQ and consume order events."""
    logger.info("Connecting to RabbitMQ at %s:%s...", settings.rabbitmq_host, settings.rabbitmq_port)

    connection = await aio_pika.connect_robust(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        login=settings.rabbitmq_user,
        password=settings.rabbitmq_pass,
    )

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            settings.rabbitmq_exchange,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        queue = await channel.declare_queue("test_order_consumer", durable=True)

        await queue.bind(exchange, routing_key="order.created")
        await queue.bind(exchange, routing_key="order.status.updated")

        logger.info("Waiting for events on queue 'test_order_consumer'...")
        logger.info("Bound to: order.created, order.status.updated")
        logger.info("Press Ctrl+C to exit")
        logger.info("-" * 60)

        await queue.consume(on_message)

        # Run forever until Ctrl+C
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Consumer stopped")
