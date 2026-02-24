# Deployment Guide

---

## 1. Local Development

### Prerequisites

| Tool | Minimum Version | Check |
|------|----------------|-------|
| Docker | 20.10 | `docker --version` |
| Docker Compose | 2.0 | `docker compose version` |
| Git | any | `git --version` |

> Python, Node.js, and PostgreSQL do **not** need to be installed locally. Everything runs inside Docker containers.

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/mduc24/ecommerce-microservices.git
cd ecommerce-microservices
```

---

### Step 2 — Configure environment files

Each service reads from its own `.env` file. Copy the examples and fill in secrets:

```bash
cp services/user-service/.env.example      services/user-service/.env
cp services/product-service/.env.example   services/product-service/.env
cp services/order-service/.env.example     services/order-service/.env
cp services/notification-service/.env.example services/notification-service/.env
cp api-gateway/.env.example                api-gateway/.env
```

**services/user-service/.env** — the only file that needs real secrets:

```bash
# Application
APP_NAME=user-service
APP_ENV=development
DEBUG=True

# Database (asyncpg driver required)
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/users_db

# JWT — change SECRET_KEY before any real deployment
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth (from console.cloud.google.com)
# Leave blank to disable Google login — email/password still works
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FRONTEND_URL=http://localhost:8080

# Server
HOST=0.0.0.0
PORT=8000
```

> **Google OAuth setup:** Create an OAuth 2.0 credential at [console.cloud.google.com](https://console.cloud.google.com/). Set the Authorized redirect URI to `http://localhost:3000/auth/google/callback`.

All other `.env` files work as-is — the example values are correct for local Docker networking.

---

### Step 3 — Start all services

```bash
docker-compose up -d
```

First run pulls images and builds all containers (~2–3 minutes). Subsequent starts are fast.

**Startup order** (enforced by `depends_on` + health checks):

```
postgres → user-service, product-service, notification-service
         → order-service (waits for product-service healthy)
         → api-gateway (waits for user-service healthy)
         → frontend (waits for api-gateway healthy)
localstack, mailhog → start independently
# After localstack healthy, run: ./scripts/setup-localstack.sh
```

Wait ~30–60 seconds after `docker-compose up` for all health checks to pass before testing.

---

### Step 4 — Run migrations

Run Alembic migrations for all four services:

```bash
docker-compose exec user-service         alembic upgrade head
docker-compose exec product-service      alembic upgrade head
docker-compose exec order-service        alembic upgrade head
docker-compose exec notification-service alembic upgrade head
```

> Migrations only need to run once on first setup, or after schema changes.

---

### Step 5 — Verify everything works

**Health check (all services in one call):**

```bash
curl http://localhost:3000/health
```

Expected: `"status": "healthy"` with all four services showing `"status": "up"`.

**Quick E2E smoke test:**

```bash
# 1. Register a user
curl -s -X POST http://localhost:3000/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Test1234!"}' | jq .

# 2. Login and grab the token
TOKEN=$(curl -s -X POST http://localhost:3000/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}' | jq -r .access_token)

# 3. Create a product
curl -s -X POST http://localhost:3000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Product","price":9.99,"stock_quantity":50,"sku":"TEST-001"}' | jq .

# 4. Place an order (triggers email + WebSocket notification)
curl -s -X POST http://localhost:3000/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"items":[{"product_id":1,"quantity":2}]}' | jq .
```

After step 4: check http://localhost:8025 (MailHog) to see the confirmation email.

---

### Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:8080 | — |
| **API Gateway** | http://localhost:3000 | — |
| **Swagger UI** | http://localhost:3000/docs | — |
| **Health Check** | http://localhost:3000/health | — |
| **LocalStack** | http://localhost:4566/_localstack/health | — |
| **MailHog** | http://localhost:8025 | — |
| **Adminer (DB GUI)** | http://localhost:3636 | System: PostgreSQL · Server: postgres · User: postgres · Pass: postgres |

---

## 2. Useful Docker Commands

### Start / Stop / Restart

```bash
# Start all services (detached)
docker-compose up -d

# Stop all services (keeps containers and volumes)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Stop and remove containers AND volumes (wipes all data)
docker-compose down -v

# Restart a single service
docker-compose restart order-service
```

### View Logs

```bash
# All services, follow live
docker-compose logs -f

# Single service, last 50 lines
docker-compose logs -f --tail=50 notification-service

# Multiple services
docker-compose logs -f api-gateway order-service
```

### Rebuild

```bash
# Rebuild a single service (e.g. after changing Dockerfile)
docker-compose up -d --build order-service

# Rebuild all services
docker-compose up -d --build
```

### Access a Service Shell

```bash
docker-compose exec user-service bash
docker-compose exec product-service bash
docker-compose exec order-service bash
docker-compose exec notification-service bash
docker-compose exec api-gateway bash
```

### Add a Python Dependency (Poetry)

```bash
# Add to a running service (no rebuild needed — uses cache volume)
docker-compose exec order-service poetry add httpx

# Restart to pick up new package
docker-compose restart order-service
```

### Add a Frontend Dependency

```bash
# Run npm via Docker — do NOT install Node.js locally
docker run --rm \
  -v $(pwd)/frontend:/app \
  -w /app \
  node:20-alpine \
  npm install axios

# Rebuild frontend container to pick up the change
docker-compose up -d --build frontend
```

---

## 3. Database Operations

### Run Migrations (all services)

```bash
docker-compose exec user-service         alembic upgrade head
docker-compose exec product-service      alembic upgrade head
docker-compose exec order-service        alembic upgrade head
docker-compose exec notification-service alembic upgrade head
```

### Create a New Migration

```bash
# Auto-generate from model changes
docker-compose exec order-service alembic revision --autogenerate -m "add_column_to_orders"

# Apply it
docker-compose exec order-service alembic upgrade head

# Roll back one step
docker-compose exec order-service alembic downgrade -1
```

### Check Migration Status

```bash
docker-compose exec order-service alembic current
docker-compose exec order-service alembic history --verbose
```

### Access via Adminer

1. Open http://localhost:3636
2. Fill in:
   - **System:** PostgreSQL
   - **Server:** `postgres`
   - **Username:** `postgres`
   - **Password:** `postgres`
   - **Database:** `users_db` (or `products_db`, `orders_db`, `notifications_db`)

### Reset Database (Nuclear Option)

Wipes all data and recreates from scratch:

```bash
# Stop everything and delete volumes
docker-compose down -v

# Start fresh (PostgreSQL runs init-databases.sql on first boot)
docker-compose up -d

# Re-run all migrations
docker-compose exec user-service         alembic upgrade head
docker-compose exec product-service      alembic upgrade head
docker-compose exec order-service        alembic upgrade head
docker-compose exec notification-service alembic upgrade head
```

---

## 4. Troubleshooting

### SQS consumer not starting

**Symptom:** `notification-service` logs show `Failed to start consumer` or no events being processed.

**Cause:** LocalStack may not be healthy yet, or `setup-localstack.sh` hasn't been run to create the SNS topic + SQS queue.

**Fix:**

```bash
# 1. Verify LocalStack is healthy
curl http://localhost:4566/_localstack/health

# 2. Run setup script (creates SNS topic + SQS queue + subscription)
./scripts/setup-localstack.sh

# 3. Restart the notification service to reconnect
docker-compose restart notification-service
```

---

### Port already in use

**Symptom:** `Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use`

**Fix:** Find and stop the conflicting process:

```bash
# macOS/Linux — find what's using the port (e.g. 5432)
lsof -i :5432

# Kill it (replace PID with actual process ID)
kill -9 <PID>

# Or stop local PostgreSQL if running
brew services stop postgresql   # macOS
sudo systemctl stop postgresql  # Linux
```

---

### Database migration failed

**Symptom:** `alembic upgrade head` fails with `relation already exists` or similar.

**Option 1 — Stamp current state (if tables exist but Alembic doesn't know):**

```bash
docker-compose exec order-service alembic stamp head
```

**Option 2 — Full reset (if data loss is acceptable):**

```bash
docker-compose down -v
docker-compose up -d
# wait for services to start, then:
docker-compose exec order-service alembic upgrade head
```

---

### Frontend not showing latest changes

**Symptom:** Code changes in `frontend/src/` aren't reflected at http://localhost:8080.

**Cause:** The frontend is a production nginx build — it doesn't hot-reload.

**Fix:** Rebuild the frontend container:

```bash
docker-compose up -d --build frontend
```

---

### Services can't reach each other

**Symptom:** Order service returns `503 Product service unavailable`.

**Cause:** Docker network issue or service not running.

**Diagnostic steps:**

```bash
# 1. Check all containers are running
docker-compose ps

# 2. Check the target service is healthy
docker-compose logs product-service | tail -20

# 3. Test connectivity from inside a container
docker-compose exec order-service curl http://product-service:8001/health

# 4. If the network is missing, recreate it
docker-compose down
docker-compose up -d
```

---

### Frontend shows blank page or 502

**Symptom:** http://localhost:8080 returns 502 or blank.

**Cause:** Either the `api-gateway` is not yet healthy, or the frontend build failed.

**Fix:**

```bash
# Check api-gateway status
docker-compose logs api-gateway | tail -20

# Rebuild frontend
docker-compose up -d --build frontend

# Check nginx is running inside the container
docker-compose exec frontend nginx -t
```

---

## 5. AWS Deployment (Planned)

> **Status:** Planned for a future phase — Terraform + ECS/EC2 setup.

When implemented, this section will cover:

- **VPC** — Public/private subnets across 2 AZs
- **ECR** — Container registry for all service images
- **ECS (Fargate)** — Managed container orchestration, no EC2 to manage
- **RDS (PostgreSQL)** — Managed database with multi-AZ failover
- **ElastiCache (Redis)** — Session cache and rate limiting
- **ALB** — Application Load Balancer replacing the API Gateway container
- **Amazon SNS + SQS** — Managed messaging (replaces LocalStack in production)
- **Secrets Manager** — Replacing `.env` files for secrets
- **CloudWatch** — Centralized logging and metrics
- **GitHub Actions** — CI/CD pipeline: lint → test → build → push to ECR → deploy to ECS

Terraform modules will live in `terraform/environments/` (dev, staging, prod).
