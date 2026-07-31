# Authentication

Authentication is handled through OTP verification.

Flow

Request OTP

↓

Verify OTP

↓

Create Account

↓

Issue JWT

↓

Authenticated Session

Roles

Player

Captain

Organization Owner

Tournament Organizer

Administrator

Permissions are enforced through dependency injection.