# Notification Service

Consumes order events from AWS SQS, sends HTML emails via SMTP, and broadcasts real-time push notifications over WebSocket. Tracks all deliveries in its own database with a retry API for failures.

**Port:** 8004 · **Database:** `notifications_db`

---

## Responsibilities

- Consume `order.created` and `order.status.updated` events from SQS (`notification-queue`)
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
| Message queue | aioboto3 (SQS long-polling consumer) |
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
| `AWS_ENDPOINT_URL` | Dev | `http://localstack:4566` (omit for production AWS) |
| `AWS_REGION` | Yes | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | Dev | `test` (use IAM role in production) |
| `AWS_SECRET_ACCESS_KEY` | Dev | `test` (use IAM role in production) |
| `SQS_QUEUE_NAME` | Yes | `notification-queue` |
| `SMTP_HOST` | Yes | `mailhog` (dev) |
| `SMTP_PORT` | Yes | `1025` (MailHog) |
| `SMTP_FROM` | Yes | Sender address (e.g. `noreply@ecommerce.com`) |

---

## Key Design Decisions

- **Delete-on-success pattern** — the SQS consumer only deletes a message after the full handler completes without exception. If processing fails (DB error, SMTP error, etc.), the message stays in the queue and SQS redelivers it after the visibility timeout. Persistent failures are recorded in the `notifications` table (`status=failed`) and retriable via `POST /notifications/retry/{id}`.
- **WebSocket `ConnectionManager` singleton** — a single `ConnectionManager` instance tracks all active WebSocket connections. It handles dead connection cleanup and broadcasts atomically. The gateway proxies `/ws/notifications` to this service's `/ws` endpoint bidirectionally.
- **SQS startup timing** — the consumer start is wrapped in a try/except during lifespan. If LocalStack/SQS isn't ready yet, the service starts without the consumer and logs an error. Restart the service once SQS is healthy to reconnect.
