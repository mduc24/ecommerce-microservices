# User Service

User management microservice for e-commerce platform with JWT authentication.

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL (async with asyncpg)
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose)
- **Password Hashing:** bcrypt (passlib)
- **Package Manager:** Poetry

## Setup

### 1. Install Dependencies

```bash
cd services/user-service
poetry install
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings (database URL, JWT secret, etc.).

### 3. Run Locally

```bash
poetry run uvicorn app.main:app --reload
```

### 4. Run with Docker Compose

From project root:

```bash
docker-compose up --build
```

## Database Migrations

This service uses Alembic for database migrations. All commands should be run from the project root.

### Create New Migration

After modifying models in `app/models.py`, generate a migration:

```bash
docker-compose exec user-service alembic revision --autogenerate -m "description of changes"
```

**Example:**
```bash
docker-compose exec user-service alembic revision --autogenerate -m "Add phone_number to users"
```

### Apply Migrations

Apply all pending migrations:

```bash
docker-compose exec user-service alembic upgrade head
```

### Rollback Migrations

Rollback one version:

```bash
docker-compose exec user-service alembic downgrade -1
```

Rollback to specific version:

```bash
docker-compose exec user-service alembic downgrade <revision_id>
```

### View Migration History

Show all migrations:

```bash
docker-compose exec user-service alembic history
```

Show current version:

```bash
docker-compose exec user-service alembic current
```

### Migration Best Practices

- ✅ **Always review** auto-generated migrations before applying
- ✅ **Test migrations** in development before applying to production
- ✅ **Commit migration files** to version control
- ✅ **Use descriptive** migration messages
- ⚠️ **Never edit** applied migrations - create new ones instead
- ⚠️ **Backup database** before running migrations in production

## API Endpoints

### Health Check

- `GET /health` - Service health status

### Authentication

- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/login` - Login and get JWT token
- `GET /api/v1/users/me` - Get current user info (requires JWT)

## Testing

Run tests:

```bash
poetry run pytest
```

Run specific test:

```bash
poetry run pytest tests/test_file.py::test_function_name
```

## Development

### Code Formatting & Linting

```bash
# Format code
poetry run ruff format .

# Lint code
poetry run ruff check .

# Lint with auto-fix
poetry run ruff check --fix .
```

## Project Structure

```
services/user-service/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry point
│   ├── models.py         # Database models
│   ├── schemas.py        # Pydantic schemas
│   ├── routes.py         # API routes
│   ├── auth.py           # JWT authentication
│   ├── database.py       # Database config
│   └── config/
│       └── settings.py   # App settings
├── alembic/              # Database migrations
├── tests/                # Tests
├── Dockerfile            # Multi-stage Docker build
├── pyproject.toml        # Poetry dependencies
└── .env.example          # Environment variables template
```

## Notes

- CORS is handled by API Gateway
- Rate limiting is a future consideration
- All passwords are hashed using bcrypt
- JWT tokens expire after 30 minutes (configurable)
- Database uses async SQLAlchemy with asyncpg driver
