# Interview Prep

---

## 60-Second Project Pitch

> _Memorize a version of this. Adjust naturally in conversation._

"I built a full-stack e-commerce platform using a microservices architecture. The backend is four independent Python/FastAPI services — users, products, orders, and notifications — each with its own PostgreSQL database, communicating through an API gateway.

The interesting part is the order processing pipeline: when a customer places an order, the order service validates stock by calling the product service synchronously, saves the order, then publishes an event to AWS SNS. The notification service polls SQS and consumes that event independently, sends an HTML email, and broadcasts a WebSocket push to the frontend — so the user sees a real-time toast notification without the order flow blocking on email delivery.

The frontend is Vue 3 with Pinia and Tailwind, Dockerized with nginx. Auth is JWT with Google OAuth 2.0. Everything runs with a single `docker-compose up`.

I built this to get hands-on experience with the patterns that appear in real distributed systems — event-driven messaging, service isolation, API gateway design, and WebSocket real-time communication."

---

## Demo Script (~10 minutes)

**Preparation:** Have these tabs open before starting.
- http://localhost:8080 (Frontend)
- http://localhost:3000/health (Health check)
- http://localhost:8025 (MailHog)
- http://localhost:4566/_localstack/health (LocalStack — SNS+SQS status)
- http://localhost:3000/docs (Swagger)

---

**Step 1 — Architecture overview (1 min)**

Open `ARCHITECTURE.md` or draw the flow on a whiteboard:
> "Here's the system. Everything comes through the API Gateway on port 3000. The gateway validates JWTs, proxies to the right backend service, and maintains a WebSocket connection to the notification service for real-time push."

---

**Step 2 — Health check (30 sec)**

```bash
curl http://localhost:3000/health | jq .
```
> "One call, parallel health checks across all four services. Status can be healthy, degraded, or unhealthy — always returns 200 so your monitoring system can read the body."

---

**Step 3 — Register and login (1 min)**

Go to http://localhost:8080 → Register page.
> "Register a user — email normalized to lowercase, password bcrypt-hashed. Click login. JWT stored in localStorage, used as Bearer token from here on."

Or show Google OAuth:
> "Google OAuth 2.0 — Authorization Code Grant with a CSRF state token in an httpOnly cookie to prevent forged callbacks."

---

**Step 4 — Browse products (30 sec)**

> "Products endpoint is public — no auth needed to browse. Paginated, filterable by category and name, sortable. The sort_by whitelist is validated server-side to prevent injection."

---

**Step 5 — Place an order (2 min) — THE KEY DEMO**

Add to cart → checkout.
> "Watch what happens: the order service calls the product service synchronously to validate stock, takes a price snapshot so the order history is immutable, saves to the database, then publishes an `order.created` event to SNS."

Switch to MailHog (http://localhost:8025):
> "Within a second or two, the notification service has polled SQS, consumed the event, and sent this HTML email. That's the async decoupling — the order API returned immediately, email happened independently."

Switch to LocalStack health (http://localhost:4566/_localstack/health):
> "LocalStack emulates SNS+SQS locally. The SNS topic fans out to the SQS queue — if I added an analytics or inventory service tomorrow, I'd just subscribe a new SQS queue to the same SNS topic without touching the order service."

Show the toast notification on the frontend:
> "And simultaneously, a WebSocket broadcast hits all connected clients. The gateway proxies the WebSocket bidirectionally — frontend connects once and gets all notifications in real time."

---

**Step 6 — Order history (30 sec)**

> "Orders page — expandable rows showing items. The product name and price here are snapshots from when the order was placed. If I change the product price now, this order still shows what the customer actually paid."

---

**Step 7 — Swagger / code (1 min)**

Open http://localhost:3000/docs:
> "FastAPI generates this automatically from Pydantic schemas. Useful for showing the full API surface."

Optionally show `services/order-service/app/services.py`:
> "Here's the `create_order` function — product validation loop, snapshot building, single DB transaction, then event publish. The event publish is wrapped in a try/except — if SNS is down, the order still succeeds. Graceful degradation."

---

**Step 8 — Wrap up (30 sec)**

> "The whole thing is `docker-compose up`. I've documented the architecture, all API endpoints, deployment steps, and the design decisions in the repo."

---

## Top 10 Technical Questions

### 1. Why microservices?

"Honestly, at this scale — four domains — a well-structured monolith would be the pragmatic choice for production. I chose microservices deliberately for the learning value: I wanted to work through the real problems — distributed data, inter-service communication, network failures, service discovery — rather than read about them.

The trade-off is real: what would be a function call in a monolith is a network request with timeout handling here. I think being upfront about that shows more technical maturity than overselling microservices as always the right answer."

---

### 2. How do services communicate?

"Two patterns. Synchronously: the order service calls the product service over HTTP using `httpx` to validate products before creating an order. It's blocking because you need an immediate, consistent answer — you can't create an order if the product doesn't exist.

Asynchronously: the order service publishes events to AWS SNS, and the notification service polls SQS to consume them. That's for anything that doesn't need to block the response — email and WebSocket notifications. The SNS topic fans out to SQS queues, so it's easy to add new consumers without touching the publisher."

---

### 3. How does authentication work?

"The user service issues JWTs on login or Google OAuth callback. The token payload has `sub` (the user ID as a string — JWT returns strings, so I convert it explicitly) and `email`.

The API Gateway validates the JWT for protected routes — it's the single security boundary, so backend services don't each need the secret key. After validation, the gateway forwards `user_id` and `email` as headers. The order service uses those to scope orders to the right user."

---

### 4. What happens when SNS is down?

"Two things. First, the order service catches publish failures and logs them — the order creation itself doesn't roll back. Orders succeed even without SNS. Second, once SNS comes back up, no events are retroactively replayed — anything published during the outage is lost.

In production I'd implement the transactional outbox pattern: write the event to the order's own database in the same transaction as the order, then have a separate process reliably publish it to SNS. That closes the gap where the order saves but the publish fails."

---

### 5. How would you scale this?

"Each service is stateless, so horizontal scaling is straightforward — run multiple replicas behind a load balancer. The API Gateway is currently the only external entry point, so in production you'd put an ALB in front of multiple gateway instances.

For the database, each service has its own PostgreSQL — you can scale them independently. A read-heavy product catalog could add read replicas without touching the order database. The notification service is CPU-light but I/O-heavy, so scaling it horizontally handles higher event volume — SQS distributes messages across multiple consumers automatically.

Redis would help for product catalog caching — most product reads are identical and don't need a DB round-trip."

---

### 6. What was the hardest problem you solved?

"The WebSocket proxy through multiple hops. The flow is: frontend → nginx → API Gateway → notification service. Each hop is a different WebSocket connection, and I needed bidirectional forwarding — messages can flow either direction.

In the gateway I use `asyncio.wait(FIRST_COMPLETED)` to wait for either the client or the backend to send a message, then forward it to the other side. The tricky part was handling disconnects cleanly — if the client disconnects, I need to close the backend connection, and vice versa, without leaving dangling coroutines."

---

### 7. What would you do differently?

"A few things. JWT in localStorage is convenient for demos but in production I'd use `httpOnly` cookies — JavaScript can't read them, so XSS can't steal the token.

I'd also implement the transactional outbox pattern for event publishing instead of fire-and-forget. And I'd add inventory decrement on order creation — right now stock is validated but never actually reduced, so two concurrent orders for the last item would both succeed.

The auth middleware being commented out for product writes is a shortcut I'd close — product management should require admin-scoped JWTs."

---

### 8. How does the WebSocket work?

"The notification service has a `ConnectionManager` singleton that tracks all active WebSocket connections. When the SQS consumer processes an event — order created or status updated — it calls `manager.broadcast()` which sends a JSON message to every connected client.

The API Gateway proxies the WebSocket at `/ws/notifications` to the notification service's `/ws` endpoint. The client connects once and receives all broadcasts. There's a ping/pong keepalive — the client sends `{type: "ping"}` every 30 seconds, server responds with `{type: "pong"}` to prevent idle disconnects."

---

### 9. What's the data snapshot pattern?

"When an order is created, I copy the product's name and price into the `order_items` table at that moment — `product_name` and `product_price` columns alongside the `product_id`. There's no foreign key to the product service's database.

This means order history is immutable. If the product's price changes tomorrow, historical orders still show what the customer actually paid. If the product is deleted, the order item still has all the display data it needs. The trade-off is that a typo in the product name at order time is preserved forever — but for a financial record, immutability is more important than current accuracy."

---

### 10. How does Google OAuth work here?

"Authorization Code Grant. The user clicks 'Sign in with Google', the browser hits `GET /auth/google` on the gateway, which proxies to the user service. The user service generates a random CSRF state token, stores it in an `httpOnly` cookie, and redirects to Google's consent screen.

Google redirects back to `/auth/google/callback?code=...&state=...`. The gateway forwards the code, state param, and the cookie to the user service. The user service does a timing-safe comparison of the cookie value against the state param — that's the CSRF check. If it passes, it exchanges the code for Google's tokens, verifies the ID token, upserts the user (create if new, link if email matches an existing account), issues a JWT, and redirects the browser to the frontend with the JWT in the query string. The frontend extracts it and stores it in localStorage."

---

## Honest Self-Assessment

### Strengths

- **End-to-end working system.** The whole flow — register, browse, order, email, WebSocket notification — works. Not a tutorial scaffold.
- **Real distributed systems patterns.** Event-driven messaging, async/await throughout, product snapshot pattern, delete-on-success SQS consumer, WebSocket proxy — these are production patterns, not toy implementations.
- **Documented trade-offs.** I've documented what I cut, why, and what the production version would look like. That's more valuable than pretending every decision was optimal.
- **Accurate documentation.** The API docs were written from the actual code, not from memory — including catching a mismatch in the retry endpoint path.

### Weaknesses

- **No tests.** The biggest gap. I built the features but didn't write pytest-asyncio unit tests or integration tests. In a real codebase this would be a blocker.
- **No inventory decrement.** Stock is validated on order creation but never reduced. The system would oversell.
- **Auth gaps.** Product write endpoints and notification endpoints are unauthenticated. This was a conscious shortcut for demo convenience.
- **Single availability zone.** Everything is on one machine. There's no failover, no replica, no backup strategy.
- **JWT in localStorage.** Simpler for demo, but XSS-vulnerable in production.

---

## What I'd Build Next

**1. Unit and integration tests (highest priority)**
pytest-asyncio for service business logic, mocked `ProductClient` for order service tests, vitest for Vue components. This is the gap that matters most for production readiness.

**2. Inventory decrement with optimistic locking**
Add a `version` column to products. Order creation calls a `reserve_stock` endpoint on the product service that atomically decrements stock using `WHERE version = :expected_version`. If the version has changed (concurrent order), retry or fail with 409. This closes the overselling problem properly.

**3. Outbox pattern for reliable event publishing**
Write order events to an `outbox` table in the same transaction as the order. A separate background process reads unpublished rows and publishes them to SNS, then marks them published. This guarantees events are never lost even if SNS is down at publish time — the order and the event are committed atomically.
