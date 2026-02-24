# Design Decisions

This document explains the *why* behind key architectural and technical choices in this project. It's intended as an honest reflection — including trade-offs and shortcuts — not just a list of positives.

---

## 1. Architecture: Why Microservices?

### The choice

I split the backend into four independent services (user, product, order, notification) instead of building a single application.

### Why I chose it

**Independent deployability.** Each service can be rebuilt, restarted, and scaled without touching the others. In practice during development, this meant I could iterate on the notification service without risking the order or product logic.

**Failure isolation.** When the notification service crashes, orders still process successfully. The SQS queue buffers events until it recovers. With a monolith, a bug in email sending could take down the entire application.

**Learning value.** Building inter-service communication, a message queue, and a WebSocket proxy forced me to solve problems (distributed state, network failures, service discovery) that don't exist in monolithic apps. These are the patterns that appear in real production systems.

### Honest trade-offs

**Complexity is real.** A feature that touches user + product + order + notification requires coordinating four services, one message broker, and a gateway. The same feature in a monolith would be a few function calls. I spent a significant amount of time on infrastructure (Docker networking, health checks, migration coordination) that a monolith wouldn't need.

**Network latency.** Every cross-service call (order → product for stock check) adds a network round-trip. In a monolith, that's a function call taking microseconds. Here it's an HTTP request with potential timeouts.

**Distributed data is hard.** There's no single database to query with a JOIN. Getting an order with its product details requires either storing snapshots (which I did) or making additional service calls at read time.

### Why not a monolith?

At this scale — a demo project with four domains — a well-structured monolith with clear module boundaries would honestly be the right choice for production. Microservices add overhead that's only justified when teams, deployment frequency, or scaling requirements demand it. I chose microservices here deliberately for the learning and demonstration value, not because the problem demanded it.

---

## 2. Why Event-Driven for Notifications?

### The choice

When an order is created, the order service publishes an event to AWS SNS. The notification service independently polls SQS and consumes it, then sends the email + WebSocket push.

### Alternatives I considered

**Direct HTTP call (order → notification):** Simple to implement. But it tightly couples the two services — if the notification service is down or slow, the order creation request fails or blocks. A user shouldn't get a failed order because the email server is slow.

**Webhooks:** Notification service would need to register itself with the order service. Adds service discovery complexity and still doesn't solve the "what happens when notification is down" problem.

**Redis Pub/Sub:** Simpler but not durable — if no subscriber is listening when the event is published, the message is lost. For email notifications, I need guaranteed delivery.

**Kafka:** More reliable and scalable, but heavily over-engineered for this use case. Kafka excels at high-throughput event streaming with replay capability. For a handful of order events per second, SNS+SQS with a durable queue is the right fit.

### Why AWS SNS + SQS

SQS provides a durable queue — events survive notification service restarts and are redelivered automatically after the visibility timeout if processing fails. The SNS fan-out model with routing via the `Subject` field (`order.created`, `order.status.updated`) is clean and extensible — I could add more SQS subscribers later (analytics, inventory, SMS) without changing the order service. In development, LocalStack emulates the full SNS+SQS API locally, and production simply removes the `AWS_ENDPOINT_URL` override to use real AWS.

### Trade-off: eventual consistency

The downside is that notification delivery is no longer synchronous with order creation. The user sees "order placed" before the email is actually sent. If the notification service is broken, the user never gets an email (though it's recorded as failed and retriable). This is the right trade-off for notifications specifically — email delay is acceptable, order creation blocking is not.

---

## 3. Database Per Service

### The choice

Four PostgreSQL databases, one per service. No service queries another service's database directly.

### Why

**Schema independence.** Each service can evolve its schema — add columns, rename tables, change data types — without coordinating with other teams or services. The notification service can add columns to track email open rates without touching the orders schema.

**Fault isolation.** A slow query in `orders_db` doesn't lock tables in `users_db`. Connection pools are scoped per service.

**Conceptual clarity.** The database boundary reinforces the service boundary. If you feel the urge to JOIN across two services' tables, that's a signal you're modelling the domain wrong.

### Honest trade-offs

**No cross-service SQL joins.** The most painful consequence. To display an order with user details, I either denormalize (store the email in the order), call the user service at read time, or accept that the order service only knows the user's ID. I chose to embed the email in the order event payload, which works but is a form of data duplication.

**Distributed consistency.** If an order is created but the notification fails to save to its database, there's no rollback mechanism. These two writes are not atomic across service boundaries. In production, a saga pattern or outbox pattern would address this — I haven't implemented either.

### In production I would...

Implement the **transactional outbox pattern** — the order service writes the event to its own database in the same transaction as the order, and a separate process reliably publishes it to SNS. This eliminates the "order saved, event lost" failure mode.

---

## 4. Data Snapshot Pattern (Orders)

### The choice

When an order is created, I copy the product's name and price into the `order_items` table at that moment. Order items store `product_name` and `product_price` as plain columns, not foreign keys to the product service.

### Why

**Price history must be immutable.** If a product's price changes tomorrow, historical orders should still reflect what the customer actually paid. If I stored only `product_id` and fetched price at read time, every price change would retroactively alter order history — which is wrong both for UX and accounting purposes.

**Product can be deleted.** If I stored a foreign key to the product service's database (which isn't even possible across service boundaries) and the product was later deleted, the order item would have a dangling reference. With snapshots, the order item is self-contained and complete.

**Read performance.** Displaying an order doesn't require calling the product service. Everything needed is in `orders_db`.

### The alternative I rejected

Always query the product service at order read time. This creates a runtime dependency for reads — if the product service is down, you can't display order history. It also makes reads slower (extra network call). The only advantage would be always showing the current product name, which is not desirable for order history.

### What I gave up

If a product name has a typo that's later corrected, the old order items will forever show the typo. This is acceptable — order history is a record of what happened, not a view of current state.

---

## 5. Technology Choices

### Python + FastAPI

I chose Python with FastAPI over Node.js/Express or Go. FastAPI gives me async/await support out of the box, automatic OpenAPI docs generation (useful for demonstrating the API during interviews), and Pydantic v2 for strong type validation. The `async def` + `await` pattern maps cleanly onto database calls, HTTP client calls, and SQS consumers — all the I/O-heavy work these services do.

SQLAlchemy 2.0's async API took some getting used to (the `execute(select(...))` pattern instead of the old `query()` style) but it's the right long-term direction for the ecosystem.

### PostgreSQL over MongoDB

The data here is relational. Orders have items. Items reference products. Users have orders. These relationships are well-expressed with foreign keys and enforced with constraints. MongoDB would give me schema flexibility I don't need, while losing the ACID guarantees I do need — especially for order creation, where I need the order and all its items committed atomically or not at all.

### Vue 3 over React

Personal preference and curiosity. Vue's Composition API with `<script setup>` is clean and less boilerplate than React hooks for this kind of CRUD-heavy frontend. Pinia is a pleasure to work with compared to Redux. This choice doesn't reflect a strong technical opinion — React would work equally well here.

### Docker Compose over Kubernetes

Docker Compose is the right tool for a local development demo. It handles service networking, health checks, dependency ordering, and volume management with minimal configuration. Kubernetes would give me production-grade orchestration (rolling deployments, auto-scaling, self-healing) but at the cost of significant complexity — Helm charts, ingress controllers, persistent volume claims, RBAC — that adds no value for a demo running on a laptop.

The Terraform directory exists as a placeholder for when this moves toward a production AWS deployment (ECS/Fargate, RDS, real SNS+SQS).

---

## 6. Authentication Design

### JWT validation at the gateway

I chose to validate JWTs in the API Gateway middleware rather than in each backend service. This centralizes the security boundary — the gateway is the only component that needs the `SECRET_KEY`, and backend services trust the `user_id` and `email` headers that the gateway forwards after validation.

The alternative — each service validates the JWT independently — would mean distributing the secret key to all services and duplicating the validation logic. The gateway-as-security-boundary is cleaner and follows the single responsibility principle.

### JWT stored in localStorage

For simplicity, the frontend stores the JWT in `localStorage`. This is the standard approach for SPAs and is straightforward to implement — Axios interceptors attach it automatically to every request.

**In production I would use `httpOnly` cookies instead.** The reason: JavaScript (and therefore XSS attacks) cannot read `httpOnly` cookies. A malicious script injected into the page can read `localStorage` and steal the token. With `httpOnly` cookies, the browser sends the cookie automatically but no JavaScript can access it. The downside is slightly more complex CORS and CSRF configuration.

### Google OAuth CSRF protection

The state parameter in the OAuth flow is a CSRF token. I generate it with `secrets.token_urlsafe()`, store it in an `httpOnly` cookie, and compare it against the callback's query parameter using `secrets.compare_digest()` (timing-safe comparison). This prevents an attacker from crafting a malicious callback URL — they can't forge the cookie value, so the state check fails.

---

## 7. API Gateway Pattern

### Why a single entry point

The frontend only needs to know one URL. Without a gateway, it would need to know the port and address of every backend service — and those would change in production when services move to different containers or hosts. The gateway provides a stable, unified interface.

The gateway also handles cross-cutting concerns that I don't want duplicated in every service: JWT validation, CORS headers, request ID injection for tracing, retry logic, and WebSocket proxying.

### Why not direct service calls from the frontend

**CORS complexity.** Every service would need to configure CORS for the frontend origin. Centralizing at the gateway means one CORS config.

**Exposing internal topology.** If the frontend calls `http://order-service:8002` directly, the internal service addresses leak to the client. In production, those addresses are private and unreachable from outside the VPC.

**No retry logic in the frontend.** The gateway's `ServiceClient` implements exponential backoff and retry for transient failures. Frontend code shouldn't be responsible for this.

### Trade-off: single point of failure

The gateway is the one thing everything depends on. If it crashes, the entire platform is inaccessible. Mitigations:
- Health check endpoint at `/health` for monitoring
- Docker `restart: unless-stopped` for automatic recovery
- In production: multiple gateway replicas behind a load balancer (ALB on AWS)

---

## 8. Known Shortcuts (Honest Assessment)

These are the things I would do differently in a production system. I'm documenting them explicitly rather than pretending they don't exist.

### Auth commented out at gateway for products and notifications

Product write endpoints (`POST`, `PUT`, `PATCH`, `DELETE /products`) and all notification endpoints are currently unauthenticated at the gateway level. The comments in the code say `# TODO: Enable auth`.

**Why I left it this way:** I wanted the demo to be easy to test without needing a token for product management. The Swagger UI is also simpler without auth on every endpoint.

**In production I would:** Enforce JWT auth on all write operations and scope product management to admin roles. Notification endpoints would also require auth or be internal-only (not exposed through the gateway at all).

### No inventory decrement on order creation

The order service validates that a product exists and has stock, but it doesn't decrement the stock quantity after the order is placed. Two concurrent orders for the same last-in-stock item would both succeed.

**In production I would:** Decrement stock atomically in the product service, or use optimistic locking with a version field. The product service would expose a `reserve` endpoint that decrements stock transactionally, and the order service would call it as part of order creation.

### No ownership check on order status updates

`PATCH /orders/{id}/status` verifies the JWT is valid but doesn't check that the order belongs to the requesting user. Any authenticated user can update any order's status.

**In production I would:** Add a role check — only admin users or internal service-to-service calls (with a service token) should be allowed to update order status.

### No rate limiting

There's no throttling on any endpoint. The register and login endpoints are particularly exposed — a bot could attempt unlimited password combinations.

**In production I would:** Add rate limiting at the gateway level using a Redis-backed counter (e.g., 5 login attempts per IP per minute, with exponential backoff on failure).

### JWT in localStorage vs httpOnly cookies

As noted in section 6 — localStorage JWTs are readable by JavaScript, making them vulnerable to XSS.

**In production I would:** Switch to `httpOnly`, `SameSite=Strict` cookies for JWT storage, add CSRF tokens for state-changing requests, and implement Content Security Policy headers to reduce XSS surface.
