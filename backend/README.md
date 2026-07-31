# CoDM Squad Hub — Backend

FastAPI backend for the African CoDM competitive platform.

## What's built so far

- **Full data model** for every locked feature: users/auth, regions, teams,
  organizations (T1-T4 roster tiers, independent from competitive tier),
  official team results vs. personal player logs (the leaderboard-integrity
  split), challenges, scrims, VOD review forms, AI weekly reviews, drill pool,
  the full transfer market (contracts, offers, market value, transfer windows),
  map guides, subscriptions, and community account reports.
- **Working auth flow**: phone + OTP signup/login, JWT issuance, minor/consent
  enforcement at signup (self-declared checkbox, per the locked decision).
  This has been tested end-to-end (see `backend/README.md` → Testing below),
  not just written.

## What's NOT built yet (next steps)

- Team creation / roster management endpoints
- Official result submission + manager-only permission checks (scaffolded
  in `app/core/deps.py` via `require_team_manager`, not wired to a router yet)
- Challenge / scrim endpoints
- VOD review form + AI weekly review generation pipeline (the actual
  Claude Sonnet 5.0 API call)
- Transfer market workflow endpoints
- WebSocket live leaderboard updates
- Push notification sending (FCM) — `fcm_device_token` field exists on User,
  no sending logic yet
- Alembic migrations (currently just `Base.metadata.create_all()` on startup,
  fine for dev, not for a real deploy with evolving schema)

## Running locally

1. Install Postgres, create a database.
2. `cp .env.example .env` and fill in `DATABASE_URL` at minimum.
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload`
5. Visit `http://localhost:8000/docs` for interactive API docs (Swagger).

## Testing

No test suite file exists yet — the auth flow above was verified manually
against a real SQLite database (request-otp → verify-otp → complete-signup →
re-login → minor consent validation → duplicate gamertag rejection, all
passing). Worth turning into a proper `pytest` suite (`tests/test_auth.py`)
before this grows much further — flag this to Claude/Grok next session.

## Notes on model design decisions

- `Team.organization_id` is nullable — a team does NOT need to belong to
  an org (locked decision).
- `Team.org_tier` and `Team.competitive_tier_mp/br` are two SEPARATE fields
  — a T2 Second Team can out-rank another org's T1 First Team on the real
  leaderboard (locked decision).
- `OfficialTeamResult.proof_screenshot_url` is required (not optional) —
  this is the dispute-resolution mechanism (locked decision).
- `PlayerMatchLog` and `OfficialTeamResult` are deliberately separate tables
  — only the manager-submitted `OfficialTeamResult` feeds the leaderboard,
  protecting it from individual players self-inflating their record.
- SMS sending (`app/services/sms.py`) is currently a dev-mode stub that logs
  the OTP code instead of sending a real text — swap in a real provider
  (Termii is a common Nigerian choice) before real users touch this.
