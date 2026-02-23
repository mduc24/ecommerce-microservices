# User Service

Handles user registration, JWT authentication, and Google OAuth 2.0 login. Issues JWT tokens consumed by the rest of the platform.

**Port:** 8003 · **Database:** `users_db`

---

## Responsibilities

- User registration with email normalization and bcrypt password hashing
- JWT login — token payload includes `sub` (user_id) and `email` claims
- Google OAuth 2.0 Authorization Code Grant with CSRF state protection
- OAuth upsert — creates or links accounts by Google ID / email
- Protected `GET /users/me` endpoint for token verification

---

## Tech Stack

| | |
|-|-|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 async + asyncpg |
| Auth | python-jose (JWT), passlib/bcrypt |
| OAuth | Authlib (Google OAuth 2.0) |
| Migrations | Alembic (async) |
| Settings | pydantic-settings |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/users/register` | No | Register new user |
| `POST` | `/api/v1/users/login` | No | Login, receive JWT token |
| `GET` | `/api/v1/users/me` | Bearer JWT | Get current user |
| `GET` | `/auth/google` | No | Initiate Google OAuth flow |
| `GET` | `/auth/google/callback` | No (CSRF cookie) | Complete OAuth, redirect with JWT |
| `GET` | `/health` | No | Health check |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@postgres:5432/users_db` |
| `SECRET_KEY` | Yes | JWT signing key — change in production |
| `ALGORITHM` | Yes | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | Token TTL (default: `30`) |
| `GOOGLE_CLIENT_ID` | For OAuth | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | For OAuth | From Google Cloud Console |
| `FRONTEND_URL` | For OAuth | Redirect target after OAuth (`http://localhost:8080`) |

---

## Key Design Decisions

- **Generic error messages on login** — both "wrong password" and "user not found" return `"Invalid email or password"`. Avoids leaking whether an email is registered.
- **bcrypt 72-byte truncation** — bcrypt silently truncates at 72 bytes. Passwords are explicitly sliced to `[:72]` before hashing to make the behavior predictable.
- **`hashed_password` is nullable** — OAuth-only users have no password set. The login route checks `not user.hashed_password` before calling `verify_password` to avoid a bcrypt error on `None`.
