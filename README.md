# E-Commerce Microservices Platform

A scalable e-commerce platform built with microservices architecture, featuring a Vue 3 storefront, Google OAuth authentication, real-time WebSocket notifications, and event-driven order processing.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5-42b883.svg)](https://vuejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-orange.svg)](https://www.rabbitmq.com/)

---

## Architecture Overview

```
                    ┌─────────────┐
                    │   Frontend   │
                    │  Vue 3 SPA  │
                    │  nginx :8080 │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ API Gateway  │
                    │  FastAPI     │
                    │   :3000     │
                    └──┬───┬───┬──┘
                       │   │   │
            ┌──────────┤   │   ├──────────┐
            │          │   │   │          │
      ┌─────▼──┐  ┌───▼───▼┐  ┌──▼───────┐
      │ User   │  │Product │  │ Order    │
      │Service │  │Service │  │ Service  │
      │ :8003  │  │ :8001  │  │ :8002   │
      └────┬───┘  └───┬────┘  └──┬──────┘
           │          │           │
           │    ┌─────▼─────┐    │  RabbitMQ
           │    │ PostgreSQL│    │◄──────────┐
           │    │  :5432    │    │           │
           └────►           ◄────┘    ┌─────▼───────┐
                └───────────┘         │Notification │
                                      │  Service    │
                                      │   :8004    │
                                      └──┬─────┬───┘
                                         │     │
                                   ┌─────▼┐  ┌─▼──────┐
                                   │ Email │  │WebSocket│
                                   │ SMTP  │  │  Push   │
                                   └──────┘  └────────┘
```

### Services

| Service | Status | Port | Database | Description |
|---------|--------|------|----------|-------------|
| **Frontend** | ✅ Complete | 8080 | - | Vue 3 SPA (nginx, Dockerized) |
| **API Gateway** | ✅ Complete | 3000 | - | Request routing, JWT validation, WebSocket proxy |
| **User Service** | ✅ Complete | 8003 | users_db | JWT authentication, Google OAuth, user management |
| **Product Service** | ✅ Complete | 8001 | products_db | Product catalog, inventory, CRUD |
| **Order Service** | ✅ Complete | 8002 | orders_db | Order processing, event publishing |
| **Notification Service** | ✅ Complete | 8004 | notifications_db | Email notifications, WebSocket push |
| **RabbitMQ** | ✅ Complete | 5672 / 15672 | - | Message broker (TOPIC exchange) |
| **MailHog** | ✅ Complete | 1025 / 8025 | - | Email capture (dev only) |
| **PostgreSQL** | ✅ Complete | 5432 | 4 databases | Shared database server |
| **Adminer** | ✅ Complete | 3636 | - | Database GUI (dev only) |

---

## Tech Stack

### Backend
- **Python 3.11** - Async/await support
- **FastAPI** - High-performance async web framework
- **SQLAlchemy 2.0** - Async ORM with connection pooling
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **aio-pika** - Async RabbitMQ client
- **aiosmtplib** - Async SMTP client
- **Jinja2** - Email templates
- **Authlib** - Google OAuth 2.0 integration

### Frontend
- **Vue 3** - Composition API with `<script setup>`
- **Vite** - Build tool with HMR
- **Tailwind CSS v4** - Utility-first CSS
- **Pinia** - State management (auth store + cart store with localStorage persistence)
- **Vue Router 4** - Client-side routing (createWebHistory)
- **Axios** - HTTP client with interceptors

### Infrastructure
- **PostgreSQL 16** - 4 independent databases
- **RabbitMQ 3** - TOPIC exchange, durable queues
- **Docker Compose** - Multi-container orchestration
- **Poetry** - Python dependency management
- **MailHog** - Email testing (dev)

### Authentication & Security
- **JWT** - Stateless authentication (email + user_id claims)
- **Bcrypt** - Password hashing (72-byte limit handled)
- **Google OAuth 2.0** - Social login via Authorization Code Grant
- **CSRF protection** - State token in `httponly` cookie, verified with `secrets.compare_digest`

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
- Order status transitions (pending → confirmed → shipped → delivered / cancelled)
- RabbitMQ event publishing on create and status update

### Notification Service
- RabbitMQ consumer for order events
- HTML email templates (Jinja2) for order confirmation and status updates
- Email delivery via SMTP (MailHog in dev)
- WebSocket broadcast for real-time push notifications
- Notification history with retry API endpoint
- Database tracking (status, error messages)

### Event-Driven Architecture
- RabbitMQ TOPIC exchange (`ecommerce_events`)
- Routing keys: `order.created`, `order.status.updated`
- Durable queue with prefetch=10
- Always-ACK pattern, errors saved to DB
- Graceful degradation (services work without RabbitMQ)

---

## Quick Start

### Prerequisites
- **Docker** >= 20.10
- **Docker Compose** >= 2.0

> No need to install Python, Node.js, or PostgreSQL locally - everything runs in Docker!

### 1. Clone and configure

```bash
git clone https://github.com/mduc24/ecommerce-microservices.git
cd ecommerce-microservices
```

Create `services/user-service/.env` with your credentials:

```bash
# services/user-service/.env
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

> **Google OAuth setup**: Create OAuth credentials at [console.cloud.google.com](https://console.cloud.google.com/), set Authorized redirect URI to `http://localhost:3000/auth/google/callback`.

### 2. Start all services

```bash
docker-compose up -d
```

All services including the frontend start together.

### 2. Access services

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:8080 |
| **API Gateway** | http://localhost:3000 |
| **API Docs (Swagger)** | http://localhost:3000/docs |
| **Health Check** | http://localhost:3000/health |
| **RabbitMQ Management** | http://localhost:15672 (admin / admin123) |
| **MailHog Web UI** | http://localhost:8025 |
| **Adminer (DB GUI)** | http://localhost:3636 (postgres / postgres) |

---

## API Endpoints

All requests go through the API Gateway at `localhost:3000`.

### Auth (Google OAuth)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/auth/google` | Redirect to Google login | No |
| `GET` | `/auth/google/callback` | Handle OAuth callback, redirect to frontend with JWT | No |

### Users

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/users/register` | Register new user | No |
| `POST` | `/users/login` | Login, get JWT token | No |
| `GET` | `/users/me` | Get current user | Yes |

### Products

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/products` | List products (paginated) | No |
| `GET` | `/products/{id}` | Get product by ID | No |
| `POST` | `/products` | Create product | No |
| `PUT` | `/products/{id}` | Update product | No |
| `PATCH` | `/products/{id}` | Partial update | No |
| `DELETE` | `/products/{id}` | Delete product | No |
| `PATCH` | `/products/{id}/stock` | Update stock | No |

### Orders

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/orders` | Create order | Yes |
| `GET` | `/orders` | List user orders | Yes |
| `GET` | `/orders/{id}` | Get order by ID | Yes |
| `PATCH` | `/orders/{id}/status` | Update order status | Yes |

`user_id` and `email` are extracted from the JWT Bearer token.

### Notifications

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/notifications` | List notifications (filtered) | No |
| `GET` | `/notifications/{id}` | Get notification by ID | No |
| `POST` | `/notifications/{id}/retry` | Retry failed notification | No |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:3000/ws/notifications` | Real-time notification push |

---

## Project Structure

```
ecommerce-microservices/
├── frontend/                          # Vue 3 SPA
│   ├── src/
│   │   ├── components/                # AppHeader, ProductCard, NotificationToast
│   │   ├── views/                     # Products, ProductDetail, Cart, Orders, Login, Register, AuthCallback
│   │   ├── stores/                    # Pinia auth store + cart store
│   │   ├── services/                  # API (axios) + WebSocket
│   │   ├── composables/               # useNotifications
│   │   ├── router/                    # Vue Router (auth guards)
│   │   ├── App.vue
│   │   └── main.js
│   ├── Dockerfile                     # Multi-stage build (node → nginx)
│   ├── nginx.conf                     # SPA fallback + /api proxy + /ws proxy
│   ├── vite.config.js
│   └── package.json
├── api-gateway/                       # FastAPI gateway
│   └── app/
│       ├── routes/                    # health, auth, users, products, orders, notifications
│       ├── middleware/                 # JWT auth
│       └── utils/                     # ServiceClient (retry + backoff)
├── services/
│   ├── user-service/                  # JWT auth, Google OAuth, user management
│   ├── product-service/               # Product CRUD, inventory
│   ├── order-service/                 # Order processing, RabbitMQ publisher
│   └── notification-service/          # Email + WebSocket notifications
│       └── app/
│           ├── events/                # RabbitMQ consumer
│           ├── services/              # Email service (aiosmtplib)
│           ├── templates/             # Jinja2 email templates
│           └── websocket/             # ConnectionManager + WS endpoint
├── scripts/
│   └── init-databases.sql             # Creates 4 PostgreSQL databases
├── docker-compose.yml                 # All services
├── docker-compose.override.yml        # Dev tools (Adminer)
└── CLAUDE.md                          # AI development instructions
```

---

## Development

### Add a dependency (via Docker)

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
docker-compose logs -f                    # All services
docker-compose logs -f notification-service  # Specific service
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
7. Order saved to DB, event published to RabbitMQ with real user email
8. Notification Service consumes event, sends HTML email (viewable at http://localhost:8025)
9. WebSocket broadcast pushes toast notification to frontend
10. Order appears on Orders page with status badge

---

## Roadmap

- [x] User Service with JWT authentication
- [x] Product Service with full CRUD
- [x] Order Service with inter-service communication
- [x] API Gateway (FastAPI proxy)
- [x] RabbitMQ event-driven messaging
- [x] Notification Service (email + DB tracking + retry)
- [x] WebSocket real-time notifications
- [x] Vue 3 frontend storefront
- [x] Frontend Dockerized (nginx, multi-stage build)
- [x] Google OAuth 2.0 (social login with CSRF protection)
- [x] JWT auth enforced on Order Service endpoints
- [ ] Inventory decrement on order creation
- [ ] Unit tests (pytest-asyncio, vitest)
- [ ] Service mesh (Istio)
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Terraform infrastructure
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Logging (ELK Stack)

---

## License

This project is licensed under the MIT License.

---

## Author

**Minh Duc** - [@mduc24](https://github.com/mduc24)
