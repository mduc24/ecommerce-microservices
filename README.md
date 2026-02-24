# E-Commerce Microservices Platform

![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![Vue.js](https://img.shields.io/badge/vue.js-3-green.svg?logo=vuedotjs)
![PostgreSQL](https://img.shields.io/badge/postgresql-%23316192.svg?style=flat&logo=postgresql&logoColor=white)
![AWS](https://img.shields.io/badge/AWS_SNS%2FSQS-LocalStack-orange.svg?style=flat&logo=amazonaws&logoColor=white)

A scalable e-commerce platform built with microservices architecture, featuring a Vue 3 storefront, Google OAuth authentication, real-time WebSocket notifications, and event-driven order processing.

---

## Key Highlights

- **Microservices architecture** — 4 independent Python/FastAPI services, each with its own PostgreSQL database, orchestrated via Docker Compose
- **Event-driven messaging** — AWS SNS→SQS fan-out decouples order processing from email/WebSocket notifications (LocalStack in dev)
- **Full-stack** — Vue 3 SPA (Tailwind CSS, Pinia, Vue Router) communicates through a single API Gateway with JWT + Google OAuth 2.0 auth

---

## Architecture

```mermaid
graph TB
    FE["Frontend<br/>Vue 3 · nginx<br/>:8080"] --> GW["API Gateway<br/>FastAPI<br/>:3000"]

    GW --> US["User Service<br/>:8003"]
    GW --> PS["Product Service<br/>:8001"]
    GW --> OS["Order Service<br/>:8002"]
    GW <-->|"WebSocket"| NS["Notification Service<br/>:8004"]

    US --> PG[("PostgreSQL<br/>:5432")]
    PS --> PG
    OS --> PG
    NS --> PG

    OS -->|"HTTP"| PS
    OS -->|"Publish events"| MQ["SNS + SQS<br/>LocalStack :4566"]
    MQ -->|"Consume events"| NS

    NS --> MH["MailHog SMTP<br/>:1025"]
```

---

## Features

### Frontend Storefront
- Login and Register pages (email/password + Google OAuth button)
- Auth-protected routes with Vue Router guards (`/cart`, `/orders`, `/products/:id`)
- Persistent auth session (JWT stored in localStorage, restored on refresh)
- Product catalog with responsive grid (2/3/4 columns)
- Product detail page with quantity selector
- Shopping cart with localStorage persistence
- Checkout flow with order creation
- Orders page with expandable details and status badges
- Real-time toast notifications via WebSocket
- Error handling with retry, loading states, empty states

### API Gateway
- Single entry point for all microservices
- Request routing and proxying with retry + exponential backoff
- JWT token validation middleware
- Google OAuth proxy routes (`/auth/google`, `/auth/google/callback`) with CSRF cookie forwarding
- Health check aggregation (parallel checks)
- WebSocket proxy for real-time notifications
- CORS configuration, request ID tracking

### User Service
- User registration with email normalization
- JWT-based authentication (login, token includes `user_id` + `email`)
- Google OAuth 2.0 (Authorization Code Grant, CSRF state protection)
- Social login creates or links accounts by Google ID / email
- Protected endpoints
- Password hashing (bcrypt); `hashed_password` nullable for OAuth-only accounts

### Product Service
- Full CRUD (create, list, get, update, patch, delete)
- Stock management endpoint
- Pagination with configurable page size
- CheckConstraints and indexes

### Order Service
- Order creation with product validation (calls product-service)
- Product snapshot pattern (name/price stored at order time)
- Order status transitions (`pending → confirmed → shipped → delivered / cancelled`)
- SNS event publishing on create and status update (aioboto3)
- `user_id` + `email` extracted from JWT Bearer token

### Notification Service
- SQS long-polling consumer for order events (aioboto3)
- HTML email templates (Jinja2) for order confirmation and status updates
- Email delivery via SMTP (MailHog in dev)
- WebSocket broadcast for real-time push notifications
- Notification history with retry API endpoint
- Database tracking (status, error messages)

### Event-Driven Architecture
- AWS SNS topic `order-events` → SQS queue `notification-queue` (LocalStack in dev)
- Event types: `order.created`, `order.status.updated`
- Long-polling consumer (`WaitTimeSeconds=20`, up to 10 messages/batch)
- Delete-on-success pattern: failures stay in queue for automatic SQS retry
- Graceful degradation (services work without SNS/LocalStack)

---

## Tech Stack

| Backend | Frontend | Infrastructure |
|---------|----------|----------------|
| Python 3.11 | Vue 3 (Composition API) | PostgreSQL 16 (4 databases) |
| FastAPI | Vite + HMR | AWS SNS + SQS (LocalStack in dev) |
| SQLAlchemy 2.0 (async) | Tailwind CSS v4 | Docker Compose |
| Alembic (async migrations) | Pinia (state management) | Poetry (dependency management) |
| Pydantic v2 | Vue Router 4 | MailHog (email testing, dev) |
| aioboto3 (SNS/SQS) | Axios (HTTP client) | Adminer (DB GUI, dev) |
| aiosmtplib + Jinja2 | | |
| Authlib (Google OAuth 2.0) | | |
| python-jose (JWT) | | |
| Bcrypt (password hashing) | | |

---

## Services & Ports

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 8080 | Vue 3 SPA served via nginx |
| **API Gateway** | 3000 | Single entry point, JWT validation, WebSocket proxy |
| **User Service** | 8003 | JWT authentication, Google OAuth, user management |
| **Product Service** | 8001 | Product catalog, inventory, CRUD |
| **Order Service** | 8002 | Order processing, SNS event publisher |
| **Notification Service** | 8004 | Email notifications, WebSocket push |
| **PostgreSQL** | 5432 | 4 independent databases |
| **LocalStack** | 4566 | AWS SNS + SQS emulation (dev only) |
| **MailHog** | 1025 / 8025 | SMTP capture / Web UI (dev only) |
| **Adminer** | 3636 | Database GUI (dev only) |

---

## Quick Start

### Prerequisites
- **Docker** >= 20.10
- **Docker Compose** >= 2.0

> No need to install Python, Node.js, or PostgreSQL locally — everything runs in Docker.

### 1. Clone

```bash
git clone https://github.com/mduc24/ecommerce-microservices.git
cd ecommerce-microservices
```

### 2. Configure

Create `services/user-service/.env`:

```bash
APP_NAME=user-service
APP_ENV=development
DEBUG=True
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/users_db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FRONTEND_URL=http://localhost:8080
```

> **Google OAuth**: Create credentials at [console.cloud.google.com](https://console.cloud.google.com/), set redirect URI to `http://localhost:3000/auth/google/callback`.

### 3. Start

```bash
docker-compose up -d
```

### 4. Access

| URL | Description |
|-----|-------------|
| http://localhost:8080 | Frontend |
| http://localhost:3000/docs | API Gateway Swagger UI |
| http://localhost:3000/health | Aggregated health check |
| http://localhost:4566/_localstack/health | LocalStack health + service status |
| http://localhost:8025 | MailHog — view sent emails |
| http://localhost:3636 | Adminer DB GUI (postgres / postgres) |

---

## API Summary

All requests go through the API Gateway at `http://localhost:3000`.

| Service | Base Path | Auth Required |
|---------|-----------|---------------|
| Google OAuth | `/auth/google`, `/auth/google/callback` | No |
| Users | `/users/register`, `/users/login`, `/users/me` | No / No / Yes |
| Products | `/products`, `/products/{id}`, `/products/{id}/stock` | No |
| Orders | `/orders`, `/orders/{id}`, `/orders/{id}/status` | Yes (JWT Bearer) |
| Notifications | `/notifications`, `/notifications/{id}` | No |
| WebSocket | `ws://localhost:3000/ws/notifications` | — |

> Full endpoint details: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

---

## Project Structure

```
ecommerce-microservices/
├── frontend/               # Vue 3 SPA (nginx, multi-stage Docker build)
├── api-gateway/            # FastAPI gateway (routing, JWT, WebSocket proxy)
├── services/
│   ├── user-service/       # JWT auth, Google OAuth, user management
│   ├── product-service/    # Product catalog, inventory, CRUD
│   ├── order-service/      # Order processing, SNS event publisher
│   └── notification-service/ # Email + WebSocket notifications
├── scripts/
│   └── init-databases.sql  # Creates 4 PostgreSQL databases
├── terraform/              # Infrastructure as Code (planned)
├── docker-compose.yml
└── docker-compose.override.yml
```

---

## Development

### Add a dependency

```bash
# Python service
docker-compose exec order-service poetry add package-name

# Frontend
docker run --rm -v $(pwd)/frontend:/app -w /app node:20-alpine npm install package-name
```

### Database migrations

```bash
docker-compose exec user-service alembic revision --autogenerate -m "description"
docker-compose exec user-service alembic upgrade head
```

### View logs

```bash
docker-compose logs -f                          # All services
docker-compose logs -f notification-service     # Specific service
```

### Run tests

```bash
docker-compose exec user-service poetry run pytest
```

---

## E2E Flow

1. Visit http://localhost:8080 → redirected to Login page
2. Login with email/password **or** click "Sign in with Google" (OAuth 2.0 flow)
3. After auth, JWT stored in localStorage; header shows username + Logout
4. Browse products, view details, add items to cart
5. Checkout (cart → order creation) — JWT sent as Bearer token
6. Order Service validates stock via Product Service, extracts `user_id` + `email` from JWT
7. Order saved to DB, event published to SNS (`order-events` topic) with real user email
8. Notification Service polls SQS, consumes event, sends HTML email (viewable at http://localhost:8025)
9. WebSocket broadcast pushes toast notification to frontend
10. Order appears on Orders page with status badge

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Detailed architecture decisions and service design |
| [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) | Full API reference for all endpoints |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Production deployment guide (Kubernetes, Terraform) |
| [DESIGN_DECISIONS.md](./DESIGN_DECISIONS.md) | Trade-offs and rationale behind key choices |

---

## Planned Improvements

- Inventory decrement on order creation (currently stock is not reduced)
- Unit & integration tests (pytest-asyncio, vitest)
- Kubernetes deployment with Helm charts
- CI/CD pipeline (GitHub Actions)
- Redis caching for product catalog
- Distributed tracing (OpenTelemetry + Jaeger)

---

## Screenshots

> _Screenshots and demo GIFs coming soon._

<!-- Add screenshots here:
![Login Page](./docs/screenshots/login.png)
![Product Catalog](./docs/screenshots/products.png)
![Orders Page](./docs/screenshots/orders.png)
-->

---

## License

This project is licensed under the MIT License.

---

**Author:** Minh Duc — [@mduc24](https://github.com/mduc24)
