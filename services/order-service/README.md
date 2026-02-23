# Order Service

Handles order creation, status management, and event publishing. Validates products via the Product Service and publishes order events to RabbitMQ for downstream processing.

**Port:** 8002 · **Database:** `orders_db`

---

## Responsibilities

- Create orders with per-product stock validation (calls Product Service)
- Store product name/price snapshot at order creation time
- Enforce order status transition rules
- Publish `order.created` and `order.status.updated` events to RabbitMQ
- Extract `user_id` and `email` from JWT Bearer token (no separate user lookup)

---

## Tech Stack

| | |
|-|-|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 async + asyncpg |
| HTTP client | httpx (via `ProductClient`) |
| Message queue | aio-pika (RabbitMQ publisher) |
| Auth | python-jose (JWT decode) |
| Migrations | Alembic (async) |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/orders` | Bearer JWT | Create order |
| `GET` | `/api/v1/orders` | Bearer JWT | List current user's orders |
| `GET` | `/api/v1/orders/{id}` | Bearer JWT | Get order by ID (user-scoped) |
| `PATCH` | `/api/v1/orders/{id}/status` | Bearer JWT | Update order status |
| `GET` | `/health` | No | Health check |

**Valid statuses:** `pending` → `confirmed` → `shipped` → `delivered` / `cancelled`
Cannot update if current status is `cancelled` or `delivered`.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@postgres:5432/orders_db` |
| `SECRET_KEY` | Yes | JWT signing key — must match user-service |
| `ALGORITHM` | Yes | JWT algorithm (default: `HS256`) |
| `PRODUCT_SERVICE_URL` | Yes | `http://product-service:8001` |
| `PRODUCT_SERVICE_TIMEOUT` | No | HTTP timeout in seconds (default: `5`) |
| `RABBITMQ_HOST` | Yes | `rabbitmq` |
| `RABBITMQ_USER` / `RABBITMQ_PASS` | Yes | `admin` / `admin123` |

---

## Key Design Decisions

- **Product snapshot pattern** — `product_name` and `product_price` are copied into `order_items` at creation time. Order history is immutable even if the product is later updated or deleted. See [DESIGN_DECISIONS.md](../../../DESIGN_DECISIONS.md#4-data-snapshot-pattern-orders).
- **Typed exception hierarchy in `ProductClient`** — `ProductNotFoundError`, `ProductServiceTimeoutError`, `ProductServiceUnavailableError` map cleanly to `404`, `504`, `503` HTTP responses. Keeps route logic free of HTTP-level concerns.
- **Graceful RabbitMQ degradation** — event publish failures are caught and logged; the order creation itself is not rolled back. Orders succeed even when RabbitMQ is temporarily unavailable.
