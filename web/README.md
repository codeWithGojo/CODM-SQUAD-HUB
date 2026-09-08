# SquadHub: multi-game organizer workspace

This update extends the August 28 CODM build with a persistent private organizer workspace. CODM is the default. PUBG Mobile, Free Fire, VALORANT, CS2, Mobile Legends, EA FC and Rocket League have editable presets. Custom games can define their own name, modes, roles, starting roster and result format.

## What works

- Separate server-stored records for each signed-in account **and** game. Browser storage holds only the preferred game selector.
- Player passports with per-game gamertag/UID uniqueness, role, country and age category; downloadable SVG cards without invented performance ratings.
- First-team, second-team, academy, ranked-grinder and community squads; roster assignment and active-competition roster locks.
- Round-robin leagues, power-of-two single-elimination brackets, and multi-round placement competitions with configurable placement/elimination points. Solo play uses one-player squads.
- Event-specific roster sizes, game modes, seasons and regions. Changing game defaults does not rewrite old events.
- Result submission, evidence links, dispute notes, manual organizer approval and immutable approved results. Knockout winners advance automatically after each round is approved.
- Separate official and practice records. Official ranking tables filter by mode, season and region and never combine incompatible event scoring systems.
- Trophy cabinet derived from completed official competitions. Tied leading records do not invent a champion.
- Internal permanent/loan roster proposals, recorded player consent, roster changes and rejection. Active rosters and transfers of minors/unconfirmed ages are blocked. Loan returns remain manual.
- Saved training drills, progress, game-specific map/strategy guides and private squad notes.
- Game record export, recent 250-action log, loading/error states and conflict detection between simultaneous tabs.
- Mobile navigation, native accessible form dialogs, keyboard focus styles, reduced-motion support and readable dark/lime styling.

`/demo` retains the previous CODM interface and all its sections. It is explicitly labelled as an archived demonstration; its sample records are not imported as real history.

## Honest launch status

The private organizer workflow is implemented. This is **not** the complete public multi-user esports platform. The old snapshot contained UI simulations, not the previously described production backend. The following remain unimplemented/unconnected and must not be advertised as active:

- Public player/organizer accounts, shared club membership, SMS/OTP identity verification, guardian verification and digital contracts.
- Shared invitations, real-time player chat and WebSocket delivery. Team Room currently stores private organizer notes.
- AI VOD analysis, scheduled weekly AI reviews and automatic training recommendations.
- Paystack payments, premium subscriptions, crowdfunding and merchandise fulfillment.
- Public CRA blacklist, moderator adjudication/appeals and independent verification.
- Publisher data feeds and independently verified player statistics.

These need actual backend/integration work and service configuration; this build does not pretend that a button click completes them. Internal roster consent is recorded by the organizer, not an independently verified signature. No payments are initiated. An evidence URL is stored as a reference, not automatically fetched or verified.

## Run and build

Requires Node 24 or newer for the native TypeScript/SQLite validation suite.

```sh
npm run install:ci
npm run build
node --test tests/workspace.test.mjs
```

The retained Vite/Vinext application targets Cloudflare Workers through Sites. `.openai/hosting.json` preserves the existing Site ID and enables its logical `DB` binding. `drizzle/0000_public_skrulls.sql` creates the database schema; apply it through the normal Sites migration/deployment flow. Schema creation never runs inside an application request.

`app/api/workspace/route.ts` requires a server-verified owner. On Sites that is the dispatcher header `oai-authenticated-user-id`. On Vercel that is the HttpOnly HMAC session cookie `csh_session` from `/api/auth/register` or `/api/auth/login`. It does not trust an owner ID supplied in JSON. Do not expose a raw Worker directly on the public internet with user-spoofable authentication headers.

Vercel is no longer a missing adapter. Set Root Directory to `web`, configure `DATABASE_URL` (Postgres) and `SESSION_SECRET`, and deploy with `web/vercel.json`. Schema is applied from `web/drizzle/postgres/` by `scripts/migrate-vercel.mjs`. Cloudflare D1 remains the Sites path. Details: [docs/VERCEL.md](../docs/VERCEL.md). This is still not a drop-in static upload.

The current live Site is not changed merely by downloading or uploading this source archive. Deploy the saved build with its D1 migration before expecting online saves to work.

## Storage and consistency

`workspaces` uses the composite primary key `(owner, game)`. Each game workspace is one versioned JSON document. All commands are validated by `lib/workspace.ts`, then persisted with a compare-and-swap SQL update. Concurrent saves cannot silently overwrite a newer record. Reload after a conflict and submit again; form input is retained. No record crosses game boundaries during a roster transfer.

A workspace has a 2 MB storage limit and a 2,000-item limit per record category. A league supports at most 20 squads, knockout and placement events at most 64. Knockout entrants must number 2, 4, 8, 16, 32 or 64; byes and group-to-knockout advancement are not implemented. Templates are organizer-editable and are not official publisher rulebooks.

Approved results are locked. Disputes must be resolved before approval. Evidence files are linked externally; upload hosting is not included. Export preserves the complete current game state; import/restore is not provided in this update.

## Validation

The automated domain/database suite covers game isolation, account isolation, duplicate gamertags/UIDs, result validation, evidence requirements, dispute resolution, immutable approvals, knockout advancement, placement scoring, roster locks, youth transfer protection, custom games, URL validation, persistence and concurrent-save conflict handling. It uses the generated migration against real SQLite.

The production build also checks the compiled API and rendered HTML with an offline SQLite binding adapter: unauthorized access, request origins, account/game isolation, reloading saved data and stale-write rejection. TypeScript checking passes. Browser interaction and real hosted authentication/database testing are separate from these checks and were not performed in this pass.
