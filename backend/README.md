# CoDM Squad Hub API

FastAPI and SQLAlchemy backend for the CoDM Squad Hub competitive platform.

## Stack

- Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2
- PostgreSQL/Supabase in production; SQLite is supported for local tests
- Alembic migrations and 54 seeded African country/zone records
- Custom phone OTP authentication with JWT access tokens
- Paystack, Termii, Gemini Flash, Firebase Cloud Messaging, and WebSockets

The OpenAPI contract is generated from the application at `/openapi.json`; interactive docs are at `/docs`.

## Local SQLite setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

For a throwaway development database, `AUTO_CREATE_TABLES=true` creates the schema and idempotently seeds regions at startup. Production should set it to `false` and run Alembic.

## PostgreSQL with Docker

From the repository root:

```bash
docker compose up --build
```

The API container waits for PostgreSQL, runs `alembic upgrade head`, then starts Uvicorn.

## Authentication bootstrap

1. `POST /api/v1/auth/request-otp`
2. `POST /api/v1/auth/verify-otp`
3. New users fetch `GET /api/v1/regions`, then call `POST /api/v1/auth/complete-signup` with the short-lived signup token.
4. Existing users receive an access token directly.

When no SMS key is configured, delivery is simulated without logging the OTP. `EXPOSE_DEV_OTP=true` returns the code only in non-production environments. Initial platform admins are assigned when their E.164 phone number is listed in `ADMIN_PHONE_NUMBERS`.

## Provider behavior

- Gemini receives structured match/VOD notes only. If no API key is configured, the rules engine generates deterministic reviews and drills.
- Paystack checkout returns `provider_configured=false` without a key; no payment is fabricated. Successful entitlements require a verified Paystack response or signed webhook.
- FCM delivery and scrim reminders are explicit admin job endpoints, intended to be invoked by a scheduler in production.
- WebSocket fan-out is process-local. A single API instance is supported as shipped; Redis/Supabase Broadcast is required before horizontal scaling.

## Migrations

```bash
alembic upgrade head
alembic current
alembic check
```

The migration chain creates all platform tables, removes Supabase Data API access from `anon` and `authenticated` for the custom-auth model, enables RLS on PostgreSQL, and seeds African regions.

## Tests

```bash
DATABASE_URL=sqlite+pysqlite:///:memory: \
AUTO_CREATE_TABLES=true \
EXPOSE_DEV_OTP=true \
PYTHONPATH=. \
.venv/bin/pytest --cov=app --cov-report=term-missing
```

The suite covers authentication/privacy hashing, organizer enforcement, challenges/rankings, Scrim Finder, tournament registration and verification, CRA sanctions/appeals, transfers, AI reviews/drills, map guides, organization permissions/trophies, Paystack entitlement idempotency, crowdfunding, merchandise stock, chat notifications, and WebSocket authorization.

## Production requirements

- Replace both default secrets and keep `EXPOSE_DEV_OTP=false`.
- Use PostgreSQL with `AUTO_CREATE_TABLES=false`.
- Configure trusted proxy handling so `request.client.host` represents the real client before relying on IP risk signals.
- Register Paystack's webhook at `/api/v1/payments/paystack/webhook`.
- Store Firebase credentials outside the image and set `FIREBASE_CREDENTIALS_PATH`.
- Add distributed rate limiting, a shared realtime broker, monitoring, backups, and scheduled job execution before a multi-instance public launch.
