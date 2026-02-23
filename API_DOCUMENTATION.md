# API Documentation

**Base URL:** `http://localhost:3000`

All requests go through the API Gateway. The gateway proxies to backend services — you never call backend ports directly.

**Authentication:** `Authorization: Bearer {token}`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Products](#2-products)
3. [Orders](#3-orders)
4. [Notifications](#4-notifications)
5. [WebSocket](#5-websocket)
6. [Health Check](#6-health-check)
7. [Error Responses](#7-error-responses)

---

## 1. Authentication

### POST /users/register

Register a new user account.

**Auth required:** No

**Request body:**

```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

| Field | Type | Rules |
|-------|------|-------|
| `email` | string | Valid email format, normalized to lowercase |
| `username` | string | 3–50 characters, must be unique |
| `password` | string | Min 8 characters |

**Response `201 Created`:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Errors:**

| Status | Detail |
|--------|--------|
| `400` | `"Email or username already exists"` |

---

### POST /users/login

Login and receive a JWT access token.

**Auth required:** No

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response `200 OK`:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**

| Status | Detail |
|--------|--------|
| `401` | `"Invalid email or password"` (also returned for inactive accounts — no distinction for security) |

---

### GET /users/me

Get the currently authenticated user.

**Auth required:** Yes — `Authorization: Bearer {token}`

**Response `200 OK`:**

```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Errors:**

| Status | Detail |
|--------|--------|
| `401` | `"Could not validate credentials"` |
| `403` | `"Not authenticated"` |

---

### GET /auth/google

Initiate Google OAuth 2.0 login flow.

**Auth required:** No

**Response:** `302 Redirect` → Google consent screen

The gateway sets an `httponly` `oauth_state` CSRF cookie on the response, which is verified in the callback step.

> Do not call this endpoint directly from frontend JavaScript — navigate the browser to this URL.

---

### GET /auth/google/callback

OAuth 2.0 callback. Handled automatically by Google after user grants consent.

**Auth required:** No

**Query params (set by Google):**

| Param | Type | Description |
|-------|------|-------------|
| `code` | string | Authorization code from Google |
| `state` | string | CSRF state token (verified against cookie) |

**Response:** `302 Redirect` → `http://localhost:8080/auth/callback?token={JWT}`

The frontend extracts the JWT from the URL and stores it in localStorage.

**Errors:**

| Status | Detail |
|--------|--------|
| `400` | CSRF state mismatch or missing code |
| `502` | User service unreachable |

---

## 2. Products

### GET /products

List products with pagination, filtering, and sorting.

**Auth required:** No

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | `20` | Items per page (1–100) |
| `offset` | int | `0` | Items to skip |
| `category` | string | — | Exact match filter |
| `is_active` | bool | — | Filter by active status |
| `name` | string | — | Case-insensitive partial match |
| `sort_by` | string | `-created_at` | `price`, `-price`, `name`, `-name`, `created_at`, `-created_at` |

**Response `200 OK`:**

```json
{
  "items": [
    {
      "id": 1,
      "name": "Wireless Bluetooth Headphones",
      "description": "High-quality wireless headphones with noise cancellation",
      "price": "29.99",
      "stock_quantity": 100,
      "sku": "WBH-001",
      "category": "Electronics",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**Errors:**

| Status | Detail |
|--------|--------|
| `400` | `"Invalid sort_by. Allowed: price, -price, ..."` |

---

### GET /products/{id}

Get a single product by ID.

**Auth required:** No

**Response `200 OK`:**

```json
{
  "id": 1,
  "name": "Wireless Bluetooth Headphones",
  "description": "High-quality wireless headphones with noise cancellation",
  "price": "29.99",
  "stock_quantity": 100,
  "sku": "WBH-001",
  "category": "Electronics",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

**Errors:**

| Status | Detail |
|--------|--------|
| `404` | `"Product not found"` |

---

### POST /products

Create a new product.

**Auth required:** No _(planned: Yes)_

**Request body:**

```json
{
  "name": "Wireless Bluetooth Headphones",
  "description": "High-quality wireless headphones with noise cancellation",
  "price": 29.99,
  "stock_quantity": 100,
  "sku": "WBH-001",
  "category": "Electronics",
  "is_active": true
}
```

| Field | Type | Rules |
|-------|------|-------|
| `name` | string | 3–200 characters, required |
| `description` | string | Max 1000 characters, optional |
| `price` | decimal | > 0, required |
| `stock_quantity` | int | >= 0, required |
| `sku` | string | 3–50 characters, unique, normalized to uppercase |
| `category` | string | Max 100 characters, optional |
| `is_active` | bool | Default `true` |

**Response `201 Created`:** Full `ProductResponse` object (same as GET /products/{id})

**Errors:**

| Status | Detail |
|--------|--------|
| `409` | `"SKU already exists"` |

---

### PUT /products/{id}

Full replacement update of a product. All fields required.

**Auth required:** No _(planned: Yes)_

**Request body:** Same as `POST /products`

**Response `200 OK`:** Full `ProductResponse` object

**Errors:**

| Status | Detail |
|--------|--------|
| `404` | `"Product not found"` |
| `409` | `"SKU already exists"` |

---

### PATCH /products/{id}

Partial update. Only provided fields are updated.

**Auth required:** No _(planned: Yes)_

**Request body (all fields optional):**

```json
{
  "price": 24.99,
  "stock_quantity": 150
}
```

**Response `200 OK`:** Full `ProductResponse` object

**Errors:**

| Status | Detail |
|--------|--------|
| `404` | `"Product not found"` |
| `409` | `"SKU already exists"` (if SKU is being changed to one that exists) |

---

### DELETE /products/{id}

Soft-delete a product (sets `is_active = false`). The record is not removed from the database.

**Auth required:** No _(planned: Yes)_

**Response `204 No Content`** — empty body

**Errors:**

| Status | Detail |
|--------|--------|
| `404` | `"Product not found"` |

---

### PATCH /products/{id}/stock

Update the stock quantity of a product (absolute value, not delta).

**Auth required:** No _(planned: Yes)_

**Request body:**

```json
{
  "stock_quantity": 50
}
```

| Field | Type | Rules |
|-------|------|-------|
| `stock_quantity` | int | >= 0, required |

**Response `200 OK`:** Full `ProductResponse` object

**Errors:**

| Status | Detail |
|--------|--------|
| `404` | `"Product not found"` |

---

## 3. Orders

All order endpoints require a valid JWT Bearer token. The order service extracts `user_id` and `email` directly from the token — no separate user ID parameter needed.

### POST /orders

Create a new order. Validates product existence and stock before saving.

**Auth required:** Yes — `Authorization: Bearer {token}`

**Request body:**

```json
{
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 3, "quantity": 1 }
  ]
}
```

| Field | Type | Rules |
|-------|------|-------|
| `items` | array | Min 1 item, required |
| `items[].product_id` | int | Must exist in product service |
| `items[].quantity` | int | > 0, required |

**Response `201 Created`:**

```json
{
  "id": 1,
  "user_id": 42,
  "status": "pending",
  "total_amount": "89.97",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00",
  "items": [
    {
      "id": 1,
      "order_id": 1,
      "product_id": 1,
      "product_name": "Wireless Bluetooth Headphones",
      "product_price": "29.99",
      "quantity": 2,
      "subtotal": "59.98",
      "created_at": "2024-01-01T00:00:00"
    },
    {
      "id": 2,
      "order_id": 1,
      "product_id": 3,
      "product_name": "USB-C Cable",
      "product_price": "29.99",
      "quantity": 1,
      "subtotal": "29.99",
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

> Product name and price are snapshotted at order time — they won't change even if the product is later updated.

**Errors:**

| Status | Detail |
|--------|--------|
| `401` | `"Could not validate credentials"` — missing or invalid JWT |
| `404` | `"Product not found"` — product ID doesn't exist |
| `503` | `"Product service unavailable"` |
| `504` | `"Product service timed out"` |

---

### GET /orders

List all orders for the authenticated user, newest first.

**Auth required:** Yes — `Authorization: Bearer {token}`

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | `0` | Records to skip |
| `limit` | int | `100` | Max records to return (1–100) |

**Response `200 OK`:** Array of `OrderResponse` objects (same structure as POST /orders response)

---

### GET /orders/{id}

Get a single order by ID. Only returns the order if it belongs to the authenticated user.

**Auth required:** Yes — `Authorization: Bearer {token}`

**Response `200 OK`:** Single `OrderResponse` object

**Errors:**

| Status | Detail |
|--------|--------|
| `401` | `"Could not validate credentials"` |
| `404` | `"Order {id} not found"` |

---

### PATCH /orders/{id}/status

Update an order's status.

**Auth required:** Yes — `Authorization: Bearer {token}` (token forwarded; no ownership check on this endpoint)

**Request body:**

```json
{
  "status": "confirmed"
}
```

| Value | Description |
|-------|-------------|
| `pending` | Initial status on creation |
| `confirmed` | Order accepted |
| `shipped` | Order dispatched |
| `delivered` | Order received |
| `cancelled` | Order cancelled |

> Cannot update if current status is `cancelled` or `delivered`.

**Response `200 OK`:** Full `OrderResponse` object with updated status

**Errors:**

| Status | Detail |
|--------|--------|
| `400` | `"Cannot update order with status: cancelled"` |
| `404` | `"Order {id} not found"` |
| `422` | Invalid status value (not in enum) |

---

## 4. Notifications

### GET /notifications

List notification records with optional filtering and pagination.

**Auth required:** No

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `recipient` | string | Filter by exact recipient email |
| `status` | string | Filter by status (`sent`, `failed`) |
| `order_id` | int | Filter by associated order ID |
| `page` | int | Page number (default: `1`) |
| `page_size` | int | Items per page, 1–100 (default: `20`) |

**Response `200 OK`:**

```json
{
  "notifications": [
    {
      "id": 1,
      "type": "order_confirmation",
      "recipient_email": "user@example.com",
      "subject": "Order #1 Confirmed",
      "order_id": 1,
      "user_id": 42,
      "status": "sent",
      "error_message": null,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 5
}
```

**Notification types:** `order_confirmation`, `order_status_update`

**Notification statuses:** `sent`, `failed`

---

### GET /notifications/{id}

Get a single notification by ID.

**Auth required:** No

**Response `200 OK`:** Single `NotificationResponse` object (same structure as above)

**Errors:**

| Status | Detail |
|--------|--------|
| `404` | `"Notification not found"` |

---

### POST /notifications/retry/{id}

Retry sending a failed notification email.

**Auth required:** No

**Request body:** None

**Response `200 OK`:** Updated `NotificationResponse` with new `status` (`sent` or `failed`)

**Errors:**

| Status | Detail |
|--------|--------|
| `400` | `"Only failed notifications can be retried"` |
| `400` | `"Unknown notification type"` |
| `404` | `"Notification not found"` |

---

## 5. WebSocket

### Connection

```
ws://localhost:3000/ws/notifications
```

The gateway proxies this connection bidirectionally to `ws://notification-service:8004/ws`.

**No authentication required** to connect (all connected clients receive broadcasts).

### Connection Lifecycle

**1. Connect**

On successful connection, the server immediately sends:

```json
{
  "type": "connected",
  "message": "Connected to notifications"
}
```

**2. Keepalive (client → server)**

Send a ping every 30 seconds to keep the connection alive:

```json
{ "type": "ping" }
```

Server responds:

```json
{ "type": "pong" }
```

**3. Notification broadcast (server → client)**

When an order event is processed, all connected clients receive:

```json
{
  "type": "notification",
  "data": {
    "event_type": "order_confirmation",
    "subject": "Order #1 Confirmed",
    "message": "Order #1 confirmed",
    "timestamp": "2024-01-01T00:00:00.000000"
  }
}
```

**4. Disconnect**

Close the WebSocket connection normally. The server cleans up the connection from `ConnectionManager` on disconnect or error.

### Example (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:3000/ws/notifications');

ws.onopen = () => console.log('Connected');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'notification') {
    console.log('New notification:', msg.data.subject);
  }
};

// Keepalive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'ping' }));
  }
}, 30000);
```

---

## 6. Health Check

### GET /health

Aggregated health check across all backend services. Always returns HTTP `200` — use the `status` field to determine overall health.

**Auth required:** No

**Response `200 OK`:**

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00.000000Z",
  "gateway": {
    "status": "up"
  },
  "services": {
    "user-service": {
      "status": "up",
      "response_time_ms": 4.21,
      "url": "http://user-service:8003/health"
    },
    "product-service": {
      "status": "up",
      "response_time_ms": 3.87,
      "url": "http://product-service:8001/health"
    },
    "order-service": {
      "status": "up",
      "response_time_ms": 5.10,
      "url": "http://order-service:8002/health"
    },
    "notification-service": {
      "status": "down",
      "error": "Connection refused",
      "url": "http://notification-service:8004/health"
    }
  }
}
```

**Overall status values:**

| Value | Meaning |
|-------|---------|
| `healthy` | All services are up |
| `degraded` | 1+ services down, but not all |
| `unhealthy` | All services are down |

Service checks run in **parallel** with a **2-second timeout** per service.

---

## 7. Error Responses

### Standard Error Format

All errors follow the same JSON structure:

```json
{
  "detail": "Error message here"
}
```

For validation errors (422), FastAPI returns a detailed breakdown:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "items"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

### Common HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | OK | Successful GET / PATCH |
| `201` | Created | Successful POST (register, create product, create order) |
| `204` | No Content | Successful DELETE |
| `400` | Bad Request | Duplicate email/username, invalid status transition, retry non-failed notification |
| `401` | Unauthorized | Missing, expired, or invalid JWT token |
| `403` | Forbidden | Valid token but insufficient permissions |
| `404` | Not Found | Resource doesn't exist or doesn't belong to current user |
| `409` | Conflict | Duplicate SKU on product create/update |
| `422` | Unprocessable Entity | Request body fails schema validation (wrong types, missing required fields) |
| `503` | Service Unavailable | Backend service (e.g. product-service) unreachable |
| `504` | Gateway Timeout | Backend service timed out (product-service default: 5s) |
