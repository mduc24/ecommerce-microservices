# API Gateway

Central API Gateway for E-Commerce Microservices Platform

## 📋 Description

The API Gateway serves as the single entry point for all client requests to the microservices platform. It handles request routing, authentication, load balancing, and provides a unified API interface.

## 🏗️ Architecture

The gateway acts as a reverse proxy, routing requests to the following backend services:

- **User Service** (Port 8003) - Authentication and user management
- **Product Service** (Port 8001) - Product catalog and inventory (planned)
- **Order Service** (Port 8002) - Order processing and cart management (planned)
- **Notification Service** (Port 8004) - Email/SMS notifications (planned)

**Gateway Port:** `3000`

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- User Service must be running

### Setup

```bash
# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
nano .env

# Run with Docker Compose (from root directory)
docker-compose up -d api-gateway
```

### Run Locally (Development)

```bash
# Install dependencies
poetry install

# Run the gateway
poetry run uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

## 📡 API Endpoints

### Health Check

- `GET /health` - Gateway health status
- `GET /health/services` - All services health status

### User Service Routes (Proxy)

- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/login` - User login (returns JWT)
- `GET /api/v1/users/me` - Get current user info (requires JWT)

### Product Service Routes (Coming Soon)

- `GET /api/v1/products` - List products
- `GET /api/v1/products/{id}` - Get product details
- `POST /api/v1/products` - Create product (admin)

### Order Service Routes (Coming Soon)

- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders` - List user orders
- `GET /api/v1/orders/{id}` - Get order details

## 🔐 Authentication

The gateway validates JWT tokens for protected endpoints and forwards them to backend services.

**Authorization Header:**
```
Authorization: Bearer <JWT_TOKEN>
```

## 🛠️ Development

### Run Tests

```bash
poetry run pytest
```

### Run with Coverage

```bash
poetry run pytest --cov=app
```

## 📝 Environment Variables

See `.env.example` for all required configuration:

- **JWT_SECRET_KEY** - Must match User Service secret
- **USER_SERVICE_URL** - User Service endpoint
- **GATEWAY_PORT** - Gateway listening port (default: 3000)
- **REQUEST_TIMEOUT** - Timeout for backend requests (seconds)
- **MAX_RETRIES** - Max retry attempts for failed requests

## 🎯 Features

- ✅ Request routing to microservices
- ✅ JWT token validation
- ✅ CORS configuration
- ✅ Request/Response logging
- ✅ Health checks
- 🔄 Rate limiting (planned)
- 🔄 Circuit breaker (planned)
- 🔄 Request caching (planned)

## 📊 Service Dependencies

```
API Gateway (Port 3000)
    ├── User Service (Port 8003) - Required
    ├── Product Service (Port 8001) - Optional
    ├── Order Service (Port 8002) - Optional
    └── Notification Service (Port 8004) - Optional
```

## 🔧 Tech Stack

- **FastAPI** - High-performance async web framework
- **HTTPX** - Async HTTP client for service communication
- **Python-JOSE** - JWT token handling
- **Pydantic** - Data validation and settings
- **Poetry** - Dependency management

## 📖 Documentation

Once running, access interactive API documentation:

- **Swagger UI:** http://localhost:3000/docs
- **ReDoc:** http://localhost:3000/redoc

## 🤝 Contributing

Follow the project's Git workflow and coding standards defined in the root CLAUDE.md file.
