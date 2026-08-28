# Delivery Roadmap

Status as of 27 August 2026.

## Implemented

| Scope | Status | Delivered |
|---|---|---|
| Sprint 3 | Complete in backend | Tournament lifecycle, organizer enforcement, registration/roster locks, brackets, reports, stats, standings, disputes, CRA blacklist and appeals |
| Sprint 4 | Complete in backend | Seasons and separate MP/BR rankings for player/team/org across national, regional, and Africa scopes |
| Sprint 5 | Complete in backend | Match analytics, structured VOD review, Gemini/rules weekly coaching, drill pool, training plans and completion |
| Sprint 6 | Complete in backend | Paystack initialize/verify/webhook, prepaid premium periods, crowdfunding, merch products/orders/stock |
| Sprint 7 | Complete in backend | Persistent notifications, FCM jobs, chat, authenticated WebSockets, admin/moderation, CI and deploy assets |
| Requested expansion | Complete in backend | Map guides, rich T1-T4 organizations, staff permissions, reputation, verified achievements, Hall of Fame, retirement, anti-abuse hashes, upgraded transfer centre |
| Mobile integration | Partial | Real OTP/signup/session, regions, live competition reads and WebSocket connection; many showcase detail screens still use prototype data |

## Required before public launch

1. Choose and connect the production PostgreSQL/Supabase project, then run `alembic upgrade head`.
2. Configure Termii, Paystack, Gemini, FCM, production CORS, callback URLs, and administrator phone numbers.
3. Register Paystack's webhook and run signed sandbox transactions for every entitlement path.
4. Connect the remaining Expo showcase screens to the typed API service and add loading, empty, error, and mutation states.
5. Replace process-local WebSocket fan-out with Redis or Supabase Broadcast before running more than one API instance.
6. Add distributed rate limiting, scheduled workers, structured logs, error reporting, metrics, backups, and restore drills.
7. Run PostgreSQL integration tests, load tests, mobile device QA, accessibility QA, and an independent security review.
8. Deploy staging, complete clan acceptance testing, then promote a pinned release to production.

## Later product phases

- Vendor marketplace and escrow design
- Player agents
- Crowdsourced ISP ratings and validation
- Richer public media, streamer, fantasy, and awards experiences
- Automated loan return/renewal workflows and recurring billing mandates

No production deployment was performed from this workspace because no CoDM Squad Hub cloud project or provider credentials were connected.
