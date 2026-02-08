# 🛒 E-Commerce Microservices Platform

A scalable, production-ready e-commerce platform built with microservices architecture, designed for AWS deployment.

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Management-blue.svg)](https://python-poetry.org/)

---

## 🏗️ Architecture Overview

This platform follows a **microservices architecture** with each service having:
- Independent database (database-per-service pattern)
- Async communication capabilities
- Docker containerization
- Independent deployment and scaling

### Current Services

| Service | Status | Port | Database | Description |
|---------|--------|------|----------|-------------|
| **User Service** | ✅ Complete | 8003 | users_db | JWT authentication, user management |
| **Product Service** | 🔄 Planned | 8001 | products_db | Product catalog, inventory |
| **Order Service** | 🔄 Planned | 8002 | orders_db | Order processing, cart management |
| **Notification Service** | 🔄 Planned | 8004 | notifications_db | Email/SMS notifications |

---

## 🚀 Tech Stack

### Backend
- **Python 3.11** - Modern async/await support
- **FastAPI** - High-performance async web framework
- **SQLAlchemy 2.0** - Async ORM
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation

### Authentication & Security
- **JWT** - Stateless authentication
- **Bcrypt** - Password hashing
- **OAuth2** - Token-based auth flow

### Database
- **PostgreSQL 16** - Relational database
- **Asyncpg** - Async PostgreSQL driver
- **Adminer** - Database GUI (dev tool)

### DevOps & Tools
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Poetry** - Dependency management
- **Git** - Version control

---

## ✨ Features

### User Service (Current)
- ✅ User registration with validation
- ✅ JWT-based authentication
- ✅ Protected endpoints
- ✅ Email normalization
- ✅ Password hashing (bcrypt)
- ✅ Async database operations
- ✅ Database migrations (Alembic)
- ✅ Comprehensive error handling
- ✅ API documentation (FastAPI auto-docs)

### Coming Soon
- 🔄 Product catalog management
- 🔄 Shopping cart functionality
- 🔄 Order processing
- 🔄 Email notifications
- 🔄 API Gateway
- 🔄 Service mesh
- 🔄 Kubernetes deployment

---

## 📋 Prerequisites

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Git**

> **Note:** No need to install Python, Poetry, or PostgreSQL locally - everything runs in Docker!

---

## 🚀 Quick Start

### 1️⃣ Clone the repository
```bash
git clone https://github.com/mduc24/ecommerce-microservices.git
cd ecommerce-microservices
```

### 2️⃣ Start all services
```bash
docker-compose up -d
```

### 3️⃣ Verify services are running
```bash
docker-compose ps
```

You should see:
- ✅ `postgres` - Running
- ✅ `user-service` - Running
- ✅ `adminer` - Running

### 4️⃣ Access services

| Service | URL | Credentials |
|---------|-----|-------------|
| **User Service API** | http://localhost:8003 | - |
| **API Docs (Swagger)** | http://localhost:8003/docs | - |
| **Adminer (DB GUI)** | http://localhost:3636 | Server: `postgres`<br>User: `postgres`<br>Password: `postgres`<br>Database: `users_db` |
| **Health Check** | http://localhost:8003/health | - |

---

## 🧪 Test the API

### Register a new user
```bash
curl -X POST http://localhost:8003/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

### Login
```bash
curl -X POST http://localhost:8003/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### Get current user (protected endpoint)
```bash
# Replace YOUR_TOKEN with the token from login response
curl http://localhost:8003/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📁 Project Structure

```
ecommerce-microservices/
├── services/                           # Microservices
│   └── user-service/                   # User authentication service
│       ├── app/                        # Application code
│       │   ├── config/                 # Configuration
│       │   │   └── settings.py         # Environment settings
│       │   ├── auth.py                 # JWT authentication
│       │   ├── database.py             # Database connection
│       │   ├── models.py               # SQLAlchemy models
│       │   ├── routes.py               # API endpoints
│       │   ├── schemas.py              # Pydantic schemas
│       │   └── main.py                 # FastAPI app
│       ├── alembic/                    # Database migrations
│       ├── tests/                      # Unit & integration tests
│       ├── Dockerfile                  # Multi-stage build
│       ├── pyproject.toml              # Poetry dependencies
│       └── README.md                   # Service documentation
├── scripts/                            # Utility scripts
│   └── init-databases.sql              # PostgreSQL initialization
├── terraform/                          # Infrastructure as Code (planned)
├── docker-compose.yml                  # Main services
├── docker-compose.override.yml         # Dev tools (Adminer)
└── .gitignore                          # Git ignore rules
```

---

## 🛠️ Development

### Setup a service for development

```bash
cd services/user-service

# Install dependencies (inside container)
docker-compose exec user-service poetry install

# Add a new dependency
docker-compose exec user-service poetry add package-name

# Restart service (picks up new dependencies)
docker-compose restart user-service
```

### Database migrations

```bash
# Create a new migration
docker-compose exec user-service alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec user-service alembic upgrade head

# Rollback
docker-compose exec user-service alembic downgrade -1
```

### Run tests

```bash
cd services/user-service
docker-compose exec user-service poetry run pytest
```

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f user-service
```

### Access database directly

```bash
docker-compose exec postgres psql -U postgres -d users_db
```

---

## 🎯 API Documentation

Each service provides interactive API documentation:

- **Swagger UI:** http://localhost:8003/docs
- **ReDoc:** http://localhost:8003/redoc

### User Service Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/users/register` | Register new user | ❌ |
| `POST` | `/api/v1/users/login` | Login and get JWT token | ❌ |
| `GET` | `/api/v1/users/me` | Get current user info | ✅ |
| `GET` | `/health` | Health check | ❌ |

---

## 🔐 Environment Variables

Each service uses environment variables for configuration:

```bash
# Copy example file
cp services/user-service/.env.example services/user-service/.env

# Edit with your values
nano services/user-service/.env
```

**Important variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

---

## 🐳 Docker Commands

### Rebuild services
```bash
docker-compose up -d --build
```

### Stop all services
```bash
docker-compose down
```

### Remove all data (including volumes)
```bash
docker-compose down -v
```

### Clean up Docker resources
```bash
docker system prune -a
```

---

## 📊 Database Schema

### Users Table (users_db)

| Column | Type | Constraints |
|--------|------|-------------|
| `id` | Integer | Primary Key |
| `email` | String(255) | Unique, Not Null |
| `username` | String(50) | Unique, Not Null |
| `hashed_password` | String(255) | Not Null |
| `is_active` | Boolean | Default: True |
| `created_at` | DateTime | Not Null |
| `updated_at` | DateTime | Not Null |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 Development Guidelines

- Always run tests before committing
- Follow Python PEP 8 style guide (enforced by Ruff)
- Write meaningful commit messages
- Update documentation for new features
- Use Poetry for dependency management
- Keep services independent and loosely coupled

---

## 🔮 Roadmap

- [x] User Service with JWT authentication
- [x] Docker Compose setup
- [x] Database migrations (Alembic)
- [x] API documentation
- [ ] Product Service
- [ ] Order Service
- [ ] Notification Service
- [ ] API Gateway (Kong/Nginx)
- [ ] Service mesh (Istio)
- [ ] Kubernetes deployment
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Terraform infrastructure
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Logging (ELK Stack)

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👨‍💻 Author

**Minh Duc**
- GitHub: [@mduc24](https://github.com/mduc24)

---

## 🙏 Acknowledgments

- FastAPI for the amazing async framework
- SQLAlchemy for powerful ORM capabilities
- Docker for containerization
- Poetry for modern Python dependency management

---

**⭐ Star this repo if you find it helpful!**
