"""
Event publisher for AWS SNS messaging.
"""

import json
import logging

import aioboto3
from pydantic import BaseModel

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes events to AWS SNS topic."""

    def __init__(self):
        self._session = aioboto3.Session()
        self._topic_arn: str | None = None

    def _client(self):
        """Return SNS async client context manager."""
        kwargs = {
            "region_name": settings.aws_region,
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }
        if settings.aws_endpoint_url:
            kwargs["endpoint_url"] = settings.aws_endpoint_url
        return self._session.client("sns", **kwargs)

    async def initialize(self):
        """Resolve SNS topic ARN from topic name (create_topic is idempotent)."""
        try:
            async with self._client() as client:
                response = await client.create_topic(Name=settings.sns_topic_name)
                self._topic_arn = response["TopicArn"]
            logger.info("SNS topic initialized: %s", self._topic_arn)
        except Exception as e:
            logger.error("Failed to initialize SNS publisher: %s", e)
            self._topic_arn = None

    async def publish(self, event: BaseModel, routing_key: str):
        """Publish an event to SNS with routing key as message attribute."""
        if not self._topic_arn:
            logger.warning("SNS not initialized. Skipping event: %s", routing_key)
            return

        try:
            async with self._client() as client:
                await client.publish(
                    TopicArn=self._topic_arn,
                    Message=json.dumps(event.model_dump()),
                    Subject=routing_key,
                    MessageAttributes={
                        "event_type": {
                            "DataType": "String",
                            "StringValue": routing_key,
                        }
                    },
                )
            logger.info("Published SNS event: %s", routing_key)
        except Exception as e:
            logger.error("Failed to publish SNS event %s: %s", routing_key, e)

    async def close(self):
        """No persistent connection to close."""
        pass


event_publisher = EventPublisher()
