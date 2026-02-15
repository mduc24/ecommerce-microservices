# Event Publishing

## Overview

Order Service publishes events to RabbitMQ for async communication between microservices.

## Events

### order.created

**Published when:** Order successfully created and committed to database.

**Routing key:** `order.created`

**Payload:**
```json
{
  "event_type": "order.created",
  "timestamp": "2026-02-15T17:28:41.878640Z",
  "data": {
    "order_id": 6,
    "user_id": 1,
    "total_amount": 79.99,
    "items": [
      {
        "product_id": 2,
        "product_name": "Wireless Keyboard",
        "quantity": 1,
        "price": 79.99
      }
    ],
    "status": "pending"
  }
}
```

### order.status.updated

**Published when:** Order status changes (e.g., pending -> confirmed -> shipped -> delivered).

**Routing key:** `order.status.updated`

**Payload:**
```json
{
  "event_type": "order.status.updated",
  "timestamp": "2026-02-15T17:28:44.927636Z",
  "data": {
    "order_id": 6,
    "old_status": "pending",
    "new_status": "confirmed",
    "updated_by": "system"
  }
}
```

## Configuration

RabbitMQ settings in `app/config/settings.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `RABBITMQ_HOST` | `rabbitmq` | RabbitMQ hostname |
| `RABBITMQ_PORT` | `5672` | AMQP port |
| `RABBITMQ_USER` | `admin` | Username |
| `RABBITMQ_PASS` | `admin123` | Password |
| `RABBITMQ_EXCHANGE` | `ecommerce_events` | Exchange name |

## Architecture

- **Exchange:** `ecommerce_events` (TOPIC, durable)
- **Messages:** Persistent (delivery_mode=2, survives RabbitMQ restart)
- **Connection:** `aio_pika.connect_robust()` with auto-reconnect
- **Error Handling:** Graceful degradation (logs warning, order still succeeds)
- **Delivery:** Round-robin across multiple consumers on the same queue

## Testing

### Run Test Consumer

```bash
docker-compose exec order-service python -m app.events.consumer
```

### RabbitMQ Management UI

- URL: http://localhost:15672
- Login: admin / admin123
- View queues, exchanges, and messages

### Test Scenarios Verified

1. **Normal flow** - Events published and consumed correctly
2. **RabbitMQ down** - Orders still created, warning logged, no crash
3. **RabbitMQ restart** - Auto-reconnect via `connect_robust()`
4. **Multiple consumers** - Round-robin delivery across consumers
