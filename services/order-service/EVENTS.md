# Event Publishing

## Overview

Order Service publishes events to AWS SNS for async communication between microservices. In development, LocalStack emulates SNS+SQS locally.

## Events

### order.created

**Published when:** Order successfully created and committed to database.

**SNS Subject / event_type:** `order.created`

**Payload:**
```json
{
  "event_type": "order.created",
  "timestamp": "2026-02-24T13:46:26.414410Z",
  "data": {
    "order_id": 20,
    "user_id": 9,
    "user_email": "user@example.com",
    "total_amount": 45.5,
    "items": [
      {
        "product_id": 3,
        "product_name": "USB-C Hub",
        "quantity": 1,
        "price": 45.5
      }
    ],
    "status": "pending"
  }
}
```

### order.status.updated

**Published when:** Order status changes (e.g., pending → confirmed → shipped → delivered).

**SNS Subject / event_type:** `order.status.updated`

**Payload:**
```json
{
  "event_type": "order.status.updated",
  "timestamp": "2026-02-24T13:46:44.927636Z",
  "data": {
    "order_id": 20,
    "user_id": 9,
    "user_email": "",
    "old_status": "pending",
    "new_status": "confirmed",
    "updated_by": "system"
  }
}
```

## Configuration

AWS/LocalStack settings in `app/config/settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `AWS_ENDPOINT_URL` | `None` | Set to `http://localstack:4566` for dev; omit for production AWS |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | `test` | Dev only — use IAM role in production |
| `AWS_SECRET_ACCESS_KEY` | `test` | Dev only — use IAM role in production |
| `SNS_TOPIC_NAME` | `order-events` | SNS topic name (ARN resolved on startup) |

## Architecture

- **Topic:** `order-events` (SNS)
- **Subscription:** `notification-queue` (SQS) subscribed to topic
- **Publisher:** `EventPublisher.initialize()` resolves topic ARN via idempotent `create_topic`; `publish()` sends with `Subject` = routing key and `event_type` MessageAttribute
- **Consumer:** `notification-service` long-polls SQS, parses SNS envelope (`Body.Message`), routes by `Subject`
- **Error Handling:** Graceful degradation — if SNS unavailable, `_topic_arn` stays `None` and publishes are silently skipped; orders still succeed

## LocalStack Setup

After starting LocalStack:

```bash
# Create SNS topic + SQS queue + subscription
./scripts/setup-localstack.sh

# Verify topic exists
aws --endpoint-url=http://localhost:4566 --region=us-east-1 sns list-topics

# Check SQS queue for messages
aws --endpoint-url=http://localhost:4566 --region=us-east-1 sqs get-queue-attributes \
  --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/notification-queue \
  --attribute-names ApproximateNumberOfMessages
```

## Test Scenarios Verified

1. **Normal flow** — SNS publish → SQS delivery → notification-service processes → email sent → message deleted
2. **SNS down at startup** — Orders still created, warning logged, no crash (graceful degradation)
3. **SNS down after startup** — Individual publishes fail with error log; order creation unaffected
4. **Consumer processing failure** — Message NOT deleted; SQS redelivers after visibility timeout
