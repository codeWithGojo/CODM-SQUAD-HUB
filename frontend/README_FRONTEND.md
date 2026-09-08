# Squad Hub Mobile Frontend

Expo / React Native client using the purple competitive-esports design system.

## Connected flows

- Real phone OTP request and verification
- New-player signup with the API-backed African region directory
- Keychain/Keystore-backed native JWT session restoration and sign-out (AsyncStorage fallback on web)
- A WebSocket client exists; this auth pass closes it on sign-out but does not start shared chat
- Live tournament discovery and current seasonal ranking reads, with an explicit showcase fallback when the API is unavailable
- Typed API adapters for transfers, performance/AI, map guides, commerce, notifications, and chat
- Hill Output analytics with swipeable player trend charts, peak/average/consistency calculations, and a six-axis role radar

The larger Tournament Control, organization, career, media, ISP, and several detail views remain polished product prototypes backed by bundled data. They are useful for UX testing but should not be described as fully API-connected yet.

## Run

```bash
npm install
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1 npx expo start
```

Use the development machine's LAN IP instead of `127.0.0.1` on a physical device.

```bash
npm run typecheck
```

When the backend runs locally without Termii, set `EXPOSE_DEV_OTP=true`; the OTP screen displays the returned local-development code. Production must keep that setting disabled.

## Track A auth handoff — September 8, 2026

The active `App.tsx` now gates the existing mobile dashboard behind phone OTP and `/auth/me`.
New players complete their profile with a signup-only token kept in memory. Only a completed
player access token is saved to native SecureStore. Returning players restore `/me` on launch
and revalidate after returning from the background. Expired/denied sessions return to login;
network failures retain credentials and offer Retry or Sign out. Authenticated API 401s also
close the player session. **More → Sign out** clears the token and closes realtime connections.
The signed-in account name and Squad Hub ID appear on More. Other prototype identities,
rosters, career records, and transfer actions still need their own API integration pass.

Under-18 signup requires a different parent/guardian phone number and declared consent.
This records contact details only: it is not SMS verification, a verified signature or legal
contract workflow. Existing accounts are not backfilled. Apply the backend migration first:

```sh
cd backend
alembic upgrade head
```

For local testing, run the backend with `EXPOSE_DEV_OTP=true` and seed/migrate its database.
The returned development code appears on the OTP screen. SMS delivery still requires provider
configuration for a real deployment. Set `EXPO_PUBLIC_API_URL` to the full `/api/v1` URL before
starting Metro or building; use your computer's LAN address for a physical phone. Restart Metro
after changing it. Native device tests must use a build including `expo-secure-store`.

Validation: `npm run typecheck`; `npm run test:auth` (Node 24+); Android Metro/Hermes export;
backend pytest against isolated SQLite; fresh and existing-schema migration checks.
Physical-device interaction, hosted API access and real SMS delivery are not verified by these checks.
Track B organizer auth and data are unchanged and are not shared with this flow.
