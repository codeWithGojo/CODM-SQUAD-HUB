# Vercel deployment for the web organizer

The Sites/Cloudflare build remains the current production target. This document is the Vercel adapter added on 8 September 2026. It is **not** a claim that a Vercel project has been created or that live saves have been verified on Vercel.

## What this adapter changes

| Concern | Sites / Cloudflare | Vercel |
|---|---|---|
| Identity | Dispatcher header `oai-authenticated-user-id` | HttpOnly HMAC session cookie `csh_session` after email/password register or login. The ChatGPT header is still accepted as a fallback. |
| Owner ID | Server-derived from the header | Server-derived from the cookie or header. JSON `owner` is ignored. |
| Database | D1 binding `env.DB` | `DATABASE_URL` Postgres (Neon, Supabase, Vercel Postgres). `json_extract` is rewritten to `body::jsonb #>> '{rules,name}'`. |
| Schema | Apply `web/drizzle/*.sql` through the Sites migration flow. Never inside a request. | `node scripts/migrate-vercel.mjs` against `web/drizzle/postgres/*.sql` during `next build`. |
| Build | `vinext` + Wrangler, Node 24 validation suite | Root Directory `web`, `npx next build`, Node 22+. `cloudflare:workers` is aliased to a stub. |

## Required Vercel project settings

1. Set the Vercel **Root Directory** to `web`.
2. Environment variables:
   - `DATABASE_URL` — Postgres connection string. Prefer a pooled URL with `sslmode=require`.
   - `SESSION_SECRET` — at least 16 random characters. Used to sign organizer cookies. Without it, cookie sign-in returns 503.
3. Optional: `SQLITE_PATH` only for local Node experiments. Do not use SQLite on Vercel; the filesystem is ephemeral.
4. Apply schema: the `web/vercel.json` build command runs `migrate-vercel.mjs` then `next build`. If `DATABASE_URL` is missing at build time the migrate step skips and saved workspaces will 503 until the variable exists and the build is replayed.

## Auth endpoints

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/register` | JSON `{ email, password, displayName }`. Password 10–200 characters. Sets `csh_session`. |
| POST | `/api/auth/login` | JSON `{ email, password }`. |
| GET | `/api/auth/me` | Session cookie or ChatGPT dispatcher headers. |
| POST | `/api/auth/logout` | Clears the cookie. |

All mutating auth and workspace routes reject cross-site `sec-fetch-site` and mismatched `Origin`. The browser workspace client now sends `credentials: "include"`.

Phone OTP remains the mobile/FastAPI product lock. This web adapter is email/password plus the existing ChatGPT Sites fallback. It is not a shared public-account, invitation, or contract system.

## Local Next.js check

```sh
cd web
npm ci
SESSION_SECRET=local-dev-session-secret SQLITE_PATH=./.vercel-dev.sqlite npx next build
```

Postgres is required for a hosted Vercel deploy. The Cloudflare `npm run build` / `vinext` path is unchanged.

## Still not done

- Public shared teams, invitations, verified identities and contracts
- Live chat, AI VOD/weekly reviews, payments, subscriptions and store fulfillment
- Full CRA blacklist, moderation, disputes and appeals on this web app
- Browser testing and live authentication/database checks against a hosted Vercel project
