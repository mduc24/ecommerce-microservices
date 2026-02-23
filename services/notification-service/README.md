# Notification Service

Consumes order events from RabbitMQ, sends HTML emails via SMTP, and broadcasts real-time push notifications over WebSocket. Tracks all deliveries in its own database with a retry API for failures.

**Port:** 8004 · **Database:** `notifications_db`

---

## Responsibilities

- Consume `order.created` and `order.status.updated` events from RabbitMQ
- Render and send HTML emails using Jinja2 templates (MailHog in dev)
- Broadcast WebSocket messages to all connected clients on each event
- Record every notification attempt (status, error message) in the database
- Expose retry API for failed notifications

---

## Tech Stack

| | |
|-|-|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 async + asyncpg |
| Message queue | aio-pika (RabbitMQ consumer) |
| Email | aiosmtplib (async SMTP) |
| Templates | Jinja2 |
| WebSocket | FastAPI WebSocket + `ConnectionManager` singleton |
| Migrations | Alembic (async) |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/notifications` | No | List notifications (filter by recipient, status, order_id) |
| `GET` | `/api/v1/notifications/{id}` | No | Get notification by ID |
| `POST` | `/api/v1/notifications/retry/{id}` | No | Retry a failed notification |
| `WS` | `/ws` | No | WebSocket — real-time notification push |
| `GET` | `/health` | No | Health check |

**List query params:** `recipient` (email), `status` (`sent`/`failed`), `order_id`, `page` (default 1), `page_size` (default 20, max 100)

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@postgres:5432/notifications_db` |
| `RABBITMQ_HOST` | Yes | `rabbitmq` |
| `RABBITMQ_USER` / `RABBITMQ_PASS` | Yes | `admin` / `admin123` |
| `RABBITMQ_EXCHANGE` | Yes | `ecommerce_events` |
| `RABBITMQ_QUEUE` | Yes | `notification_queue` |
| `SMTP_HOST` | Yes | `mailhog` (dev) |
| `SMTP_PORT` | Yes | `1025` (MailHog) |
| `SMTP_FROM` | Yes | Sender address (e.g. `noreply@ecommerce.com`) |

---

## Key Design Decisions

- **Always-ACK pattern** — the RabbitMQ consumer always ACKs messages, even on failure. Errors are recorded in the `notifications` table (`status=failed`, `error_message` set). Failed notifications are retriable via `POST /notifications/retry/{id}`. This avoids infinite requeue loops for messages that will always fail (e.g., invalid email address).
- **WebSocket `ConnectionManager` singleton** — a single `ConnectionManager` instance tracks all active WebSocket connections. It handles dead connection cleanup and broadcasts atomically. The gateway proxies `/ws/notifications` to this service's `/ws` endpoint bidirectionally.
- **RabbitMQ startup timing** — the consumer start is wrapped in a try/except during lifespan. If RabbitMQ isn't ready yet, the service starts without the consumer and logs an error. Restart the service once RabbitMQ is healthy to reconnect.
