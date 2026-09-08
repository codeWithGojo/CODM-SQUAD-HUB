# CoDM Squad Hub

## September 8, 2026: multi-game web organizer

Today's web application is in [web/](web/README.md). It adds separate account/game workspaces, editable game presets, player records, squads, league/knockout/placement competitions, result review, rankings, internal roster proposals, training and guides. The existing `backend/` and `frontend/` remain separate codebases; the new web app is not connected to that FastAPI backend.

Validation for this source: 11 domain/database tests plus 1 compiled-artifact test passed, TypeScript passed, and the compiled Worker passed offline authentication/origin/persistence/isolation/conflict checks. Browser interaction and real hosted authentication/database testing remain outstanding.

The web app still targets Sites/Cloudflare with authenticated dispatcher identity and a D1 database migration. A Vercel adapter is now in the tree: HMAC session cookies, a Postgres/`DATABASE_URL` driver, Next.js Node build config, and organizer email/password routes. See [docs/VERCEL.md](docs/VERCEL.md). It is still **not** a live hosted Vercel deployment — `DATABASE_URL` and `SESSION_SECRET` must be supplied on a Vercel project whose Root Directory is `web`.

Remaining public-platform work: shared player/organizer accounts and memberships; verified identity/consent and contracts; real-time chat; AI VOD/weekly reviews; payments/subscriptions/crowdfunding/store fulfillment; public CRA moderation and appeals; verified publisher/statistics feeds. Additional organizer limitations include manual loan returns, no evidence uploads or import/restore, and no byes or group-to-knockout formats. See [web/README.md](web/README.md) for the full scope and limitations.

The older implementation summary below describes the retained backend/mobile code. It does not imply those integrations are deployed or connected to the new web app.


CoDM Squad Hub is a mobile-first competitive infrastructure platform for the African Call of Duty: Mobile scene. It combines player identity, teams and organizations, official competition records, rankings, training, commerce, communications, and governance in one system.

## Implemented platform scope

The FastAPI backend now includes:

- Phone OTP authentication, JWT sessions, player profiles, teams, and organization rosters
- Tournament organizer applications and enforced organizer permissions
- Tournament lifecycle, registration, roster locks, brackets, match reports, verified stats, standings, disputes, and CRA blacklist appeals
- Seasonal MP/BR rankings for players, teams, and organizations at country, African-region, and continental scope
- Challenges and Scrim Finder, with bilateral result confirmation before a challenge enters the official ledger
- Structured VOD reviews, weekly AI coaching, performance analytics, and generated training drills using Gemini Flash or a deterministic fallback
- Hardpoint hill-by-hill player output, shared-scale trend charts, consistency/streakiness analysis, and role radar profiles
- Paystack checkout/verification/webhooks, prepaid team premium periods, crowdfunding, merchandise orders, and stock reservation
- Persistent notifications, FCM delivery jobs, chat, authenticated WebSockets, moderation, audit logs, and an admin dashboard
- Curated PDF/YouTube map guides plus private team guide slots
- T1-T4 organization rosters, staff permissions, reputation, verified achievements, Hall of Fame, promotions, and retirement history
- Transfer offers, counteroffers, player consent, offer expiration, loans/free signings, watchlists, rumours, transfer windows, sanctions, and market-value snapshots
- HMAC-hashed IP/device anti-abuse evidence; raw fingerprints are never stored

The Expo app is connected to the real API for OTP, onboarding, session restoration, region discovery, live tournaments/rankings, and authenticated WebSocket startup. Some large showcase/detail screens still use bundled prototype data and must be connected endpoint by endpoint before a public release.

## Run locally

The quickest full-stack backend setup uses Docker:

```bash
docker compose up --build
```

The API is then available at `http://localhost:8000`, with Swagger at `http://localhost:8000/docs`.

Run the mobile app separately:

```bash
cd frontend
npm install
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1 npx expo start
```

For a physical phone, replace `127.0.0.1` with the development machine's LAN address.

## Verify the build

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt
DATABASE_URL=sqlite+pysqlite:///:memory: AUTO_CREATE_TABLES=true EXPOSE_DEV_OTP=true PYTHONPATH=. .venv/bin/pytest

cd ../frontend
npm ci
npm run typecheck
```

## Deployment status

Docker, Alembic, GitHub Actions, Compose, and a Render blueprint are included. No production environment has been deployed from this workspace: database credentials and provider keys still need to be supplied, migrations applied to the chosen PostgreSQL/Supabase project, and Paystack/Termii/FCM webhooks or credentials configured.

See [backend/README.md](backend/README.md) for operational details and [docs/ROADMAP.md](docs/ROADMAP.md) for the remaining launch work.
