# Share CoDM Squad Hub with EAS

EAS builds an installable Android APK (and optional iOS IPA) that you send to testers. Config: `frontend/eas.json`.

## One-time setup

1. Create a free account at https://expo.dev
2. In the `frontend` folder:

```bash
cd frontend
npm install
npx eas-cli login
npx eas-cli init
```

`eas init` writes `extra.eas.projectId` into `app.json`. Commit that change.

3. Point preview builds at your **live API**. Phones cannot use localhost. Edit `frontend/eas.json`:

```json
"EXPO_PUBLIC_API_URL": "https://your-api.onrender.com/api/v1"
```

Deploy FastAPI first, or testers only see showcase/demo data.

## Share an Android APK (easiest)

```bash
cd frontend
npx eas-cli build --profile preview --platform android
```

Expo then gives you a page with a QR code and an APK download link. Send that link. Testers install the APK (Android may ask to allow unknown sources). No Play Store listing is required — `preview` uses internal distribution.

## iOS testers

Needs a paid Apple Developer account and registered devices or TestFlight.

```bash
npx eas-cli build --profile preview --platform ios
```

## Profiles

- `preview` — testers / friends (internal APK + IPA)
- `production` — Play Store AAB / App Store IPA
- `development` — your own live-reload client

Builds also appear at https://expo.dev under the project → Builds.

Keep `EXPOSE_DEV_OTP=false` on any shared API. Testers need real SMS OTP (Termii).
