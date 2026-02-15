# Chat 5 Handoff - Order Service Complete

## Branch
`feature/order-service` (15 commits, 26 files changed, +1453 lines)

## What Was Built

### Order Service (`services/order-service/`)
Full CRUD order processing microservice with inter-service communication.

**Stack:** FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Alembic, httpx

**Files Created:**
| File | Purpose |
|------|---------|
| `app/config/settings.py` | Pydantic v2 settings with product_service_url |
| `app/database.py` | Async engine with connection pooling |
| `app/models.py` | Order + OrderItem models with constraints |
| `app/schemas.py` | OrderStatus enum, request/response schemas |
| `app/services.py` | Business logic (create, get, list, update status) |
| `app/routes.py` | 4 CRUD endpoints + health check |
| `app/main.py` | FastAPI app with lifespan, CORS, health check |
| `app/clients/product_client.py` | HTTP client with custom exception hierarchy |
| `alembic/` | Async migrations (orders + order_items tables) |
| `Dockerfile` | Multi-stage (base → development → production) |

### API Gateway Updates
- `api-gateway/app/routes/orders.py` - 4 proxy routes
- `api-gateway/app/main.py` - orders router registered

### Docker Compose
- `order-service` added with depends_on: postgres + product-service

## Database Schema

### orders
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | Auto-increment |
| user_id | Integer | Indexed, no FK (microservices) |
| status | String(20) | Indexed, default "pending" |
| total_amount | Numeric(10,2) | CHECK >= 0 |
| created_at | DateTime | |
| updated_at | DateTime | |

### order_items
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| order_id | Integer FK | CASCADE delete |
| product_id | Integer | No FK (microservices) |
| product_name | String(255) | Snapshot at order time |
| product_price | Numeric(10,2) | Snapshot, CHECK > 0 |
| quantity | Integer | CHECK > 0 |
| subtotal | Numeric(10,2) | CHECK > 0 |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/orders?user_id=N | Create order |
| GET | /api/v1/orders?user_id=N | List user orders |
| GET | /api/v1/orders/{id}?user_id=N | Get order detail |
| PATCH | /api/v1/orders/{id}/status | Update status |
| GET | /api/v1/orders/health | Route health check |
| GET | /health | Service health + DB status |

**Note:** user_id is query param (TODO: replace with JWT token)

## Status Transitions
- pending → confirmed → shipped → delivered
- Any status → cancelled
- Cannot update if current status is "cancelled" or "delivered"

## Inter-Service Communication
- Order Service → Product Service via httpx (ProductClient)
- Custom exceptions: ProductNotFoundError, ProductServiceUnavailableError, ProductServiceTimeoutError
- Product data snapshot pattern (name/price captured at order time)

## Port Assignments
| Service | Port |
|---------|------|
| Product Service | 8001 |
| Order Service | 8002 |
| User Service | 8003 |
| API Gateway | 3000 |
| PostgreSQL | 5432 |

## Test Results (Manual)

### Happy Path (4/4 passed)
- Create order with 2 items → 201, total=$205.48
- Get order detail → 200, items loaded
- List orders → 200, array with items
- Update status → 200, pending → confirmed

### Error Scenarios (6/6 passed)
- Product not found → 404
- Insufficient stock → 400
- Order not found → 404
- Invalid status transition (delivered → shipped) → 400
- Empty items list → 422
- Quantity = 0 → 422

## Known Issues / TODOs
1. **No unit tests** - tests/ directory has no automated tests yet
2. **user_id as query param** - needs JWT integration
3. **No stock decrement** - product stock not reduced on order creation
4. **No event publishing** - no RabbitMQ/message queue integration yet

## Ready for Next Chat
- **RabbitMQ integration** - events: OrderCreated, OrderStatusUpdated
- **Inventory decrement** - reduce product stock on order creation
- **Unit tests** - pytest with async fixtures, mocked ProductClient
- **Notification Service** - consume order events
