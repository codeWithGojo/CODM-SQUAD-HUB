# Authentication and Roles

The application uses custom phone OTP authentication and signed JWTs.

New users select one of the 54 seeded African regions. Minor accounts require a parental-consent confirmation. Native sessions are stored through Expo SecureStore (iOS Keychain / Android Keystore-backed storage); AsyncStorage is retained only as a web-development fallback and one-time native migration source.

Authorization capabilities are additive and server-verified:

- Player/user
- Direct team manager or active manager membership
- Organization owner or staff member with explicit permissions
- Approved Tournament Organizer application
- Platform administrator
- Chat participant, payment owner, or transfer participant for resource-specific access

The client never grants a role by hiding or showing a button; every protected operation checks the database on the backend.
