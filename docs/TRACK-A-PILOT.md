# Track A pilot: mobile builds and hosted API

Track A remains the Expo player/org app plus FastAPI. Track B is the separate browser organizer under `web/`; their sessions and databases are not merged.

## Targets

| Surface | Target | Configuration |
| --- | --- | --- |
| Android/iPhone | Expo EAS Build | `frontend/eas.json`, application identifier `africa.codmsquadhub.app` |
| FastAPI | Render Docker web service | Root `render.yaml`; container applies Alembic migrations before Uvicorn |
| Database | Managed PostgreSQL | Set backend `DATABASE_URL`; SQLite remains local/test only |
| Browser organizer | Existing `web/` Vercel/Sites paths | Independent of this Track A change |

The Render service and EAS build are not created by pushing source to GitHub. No running deployment or installable APK is claimed in this pass.

## Prepare deployment

1. Connect the owner's Render account and GitHub repository. Review the database/service plan before provisioning paid resources.
2. Supply a PostgreSQL `DATABASE_URL`, appropriate `CORS_ORIGINS`, and the existing SMS provider credentials. Render generates JWT and anti-abuse secrets. Production keeps `EXPOSE_DEV_OTP=false`. AI/payment keys are not required for this pilot.
3. Deploy `codm-squad-hub-api`, check `/health`, and run the OTP/login tests against the hosted service.
4. Link `frontend/` to the owner's Expo project. Set `EXPO_PUBLIC_API_URL` to the actual HTTPS backend URL ending in `/api/v1` in the EAS environment. A pre-install guard blocks missing/placeholder URLs.
5. Run `eas build --profile preview --platform android` from `frontend/` for an internal APK. iOS builds require the appropriate Apple signing/provisioning setup. Verify sign-in and saves on physical devices before inviting the clan.

## Saved organization workflow

Use **Operations → ORG HQ** or **More → Manage Organization**:

- Create an organization and individual T1 First / T2 Second / T3 Academy / T4 Development squads. Structure is separate from competitive ranking. Standalone MP/BR squads remain supported.
- Find an existing player by their exact Squad Hub ID, review the matched name and add them as Player or Substitute. This directly edits a roster; it is not an invitation, verified consent, payment or contract.
- Owners/authorized managers can move players between their organization's squads. Promotions/demotions are derived from structural tier direction on the server and recorded in the player's timeline. Individual result/stat records are preserved.
- Manager assignment cannot be smuggled through player-add/move operations. Active event locks block roster changes. Active contracts cannot be silently terminated using Remove.
- Reload organizations/squads from the API. Names/SHIDs are shown without exposing phone, email or guardian contact details.
- **Career → History** shows the authenticated player's real roster history. Other career/performance sections retain sample data and need later integration.

## Checks in this pass

Backend tests cover owner/outsider permissions, T1–T4 creation, standalone squads, saved rosters, exact SHID lookup/privacy, duplicate membership, promotion history, repeat moves, active-event locks and contracted-player removal. Frontend TypeScript and Android export verify compilation. Hosted/PostgreSQL concurrency and physical-device interaction remain separate pilot checks.

Next: connect the Transfer Centre UI to its existing offer/consent endpoints. Keep Naira-only money rules and preserve official-vs-practice result separation.
