# Security Model

## Authentication

- Phone numbers must use E.164 format.
- OTP values are generated with `SystemRandom`, stored only as HMAC-SHA256 hashes, expire after ten minutes by default, are one-use, and allow five attempts.
- A phone cannot request another code until the configured cooldown passes.
- New-user signup tokens expire after 15 minutes; access tokens default to seven days.
- Production startup refuses the repository's default JWT or anti-abuse secrets.
- Banned accounts are rejected by both HTTP authentication and WebSocket authentication.

## Authorization

Authorization is server-side and resource-scoped. Platform admins, approved tournament organizers, direct team managers, organization owners, staff permission grants, players, payment owners, and chat participants each have separate checks. Organizer approval is a persisted admin-reviewed role, not a client flag.

Sensitive state machines reject invalid transitions: tournament lifecycle, registration capacity, verified match edits, disputes, transfer negotiations, campaign/order status, and Paystack entitlements.

## Anti-abuse evidence

The platform stores HMAC hashes of the normalized client IP, device fingerprint header, and phone where appropriate. It never stores raw IP addresses or raw device identifiers in the anti-abuse fields. The HMAC uses a secret separate from the JWT secret so hashes cannot be reproduced from a database leak alone.

The application intentionally does not trust `X-Forwarded-For` directly. Production proxy allowlists must be configured at the ASGI server/load balancer so `request.client.host` is normalized by trusted infrastructure.

## Realtime

JWTs are sent in the first WebSocket message, not the query string, avoiding token leakage in proxy access logs. Authentication must complete in ten seconds. Every requested channel is authorized against fresh database state, including current ban status.

## Payments

Paystack webhooks are verified using HMAC-SHA512 over the raw body. The stored expected amount and currency must match provider data before an entitlement is granted. Processing is idempotent and provider secrets stay server-side.

## Database boundary

The app uses direct SQLAlchemy connections and custom JWT auth. On PostgreSQL, the hardening migration enables RLS and revokes all table privileges from Supabase `anon` and `authenticated` roles. The backend database role remains responsible for enforcing FastAPI authorization.

## Before production

- Add distributed rate limiting by IP/device/phone and a WAF; the current cooldown is per phone and process/database only.
- Configure a trusted proxy allowlist, HTTPS, HSTS, secure secret rotation, database least privilege, encrypted backups, and restore testing.
- Move scheduled work to a durable queue and replace process-local WebSockets before scaling horizontally.
- Add dependency/container scanning, structured redaction, alerting, incident procedures, and an independent penetration test.
- Keep `EXPOSE_DEV_OTP=false` and never place provider keys in the mobile bundle.
