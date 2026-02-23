# Product Service

Manages the product catalog. Provides full CRUD, stock management, and paginated listing with filtering and sorting.

**Port:** 8001 · **Database:** `products_db`

---

## Responsibilities

- Create, read, update, and soft-delete products
- Stock quantity management (absolute value updates)
- Paginated listing with filter (category, name, is_active) and sort support
- SKU uniqueness enforcement (normalized to uppercase)
- Serves product data to the Order Service on order creation (internal HTTP)

---

## Tech Stack

| | |
|-|-|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 async + asyncpg |
| Price type | `Numeric(10, 2)` — exact decimal, no float rounding |
| Migrations | Alembic (async) |
| Settings | pydantic-settings |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/products` | No | List products (paginated, filterable) |
| `GET` | `/api/v1/products/{id}` | No | Get product by ID |
| `POST` | `/api/v1/products` | No* | Create product |
| `PUT` | `/api/v1/products/{id}` | No* | Full update |
| `PATCH` | `/api/v1/products/{id}` | No* | Partial update |
| `DELETE` | `/api/v1/products/{id}` | No* | Soft delete (sets `is_active=false`) |
| `PATCH` | `/api/v1/products/{id}/stock` | No* | Update stock quantity |
| `GET` | `/health` | No | Health check |

_*Auth planned — not yet enforced_

**List query params:** `limit` (default 20, max 100), `offset`, `category`, `is_active`, `name` (partial match), `sort_by` (`price`, `-price`, `name`, `-name`, `created_at`, `-created_at`)

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@postgres:5432/products_db` |
| `DEFAULT_PAGE_SIZE` | No | Default items per page (default: `20`) |
| `MAX_PAGE_SIZE` | No | Max items per page (default: `100`) |

---

## Key Design Decisions

- **Soft delete, not hard delete** — `DELETE /products/{id}` sets `is_active=false` rather than removing the row. Existing order items that snapshot this product's name/price remain valid, and the product can be reactivated without data loss.
- **`Numeric(10, 2)` for price** — using PostgreSQL's `NUMERIC` type (not `FLOAT`) ensures exact decimal arithmetic. Floating-point types can introduce rounding errors in financial calculations.
- **Sort whitelist** — `sort_by` values are validated against an explicit allowlist (`ALLOWED_SORT_FIELDS`). Arbitrary column names from query params are never passed to SQLAlchemy, preventing potential injection.
