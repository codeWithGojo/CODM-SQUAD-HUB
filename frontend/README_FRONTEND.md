# Squad Hub Mobile Frontend

Expo / React Native client using the purple competitive-esports design system.

## Connected flows

- Real phone OTP request and verification
- New-player signup with the API-backed African region directory
- Keychain/Keystore-backed native JWT session restoration and sign-out (AsyncStorage fallback on web)
- Authenticated WebSocket connection with reconnect/cleanup handling
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
