# Privacy Notes

CoDM Squad Hub is designed to minimize anti-abuse data while retaining enough evidence to investigate account compromise, ban evasion, and competitive misconduct.

## Data stored

- Account identity: phone number, optional email, gamertag, player ID, region, declared age category, and consent confirmation
- Competitive records: memberships, contracts, results, stats, rankings, transfers, disputes, sanctions, achievements, and career timeline
- Development data: player-entered match logs, coach metrics, structured VOD notes, AI output, and drill completion
- Commerce: Paystack references/status/amounts, campaign contributions, order items, and delivery details
- Communications: notifications, chat messages, attachments metadata, and device push token
- Security evidence: HMAC hashes of phone/IP/device signals, event type, risk score, and limited investigation notes

Raw IP addresses and raw device fingerprints are not persisted in the anti-abuse fields. OTP codes and payment secrets are never stored in plaintext application records.

## External processors

- Termii receives the phone number and OTP message when SMS is configured.
- Paystack receives checkout identity, amount, reference, and transaction metadata.
- Gemini receives structured competitive statistics and coach notes, not raw video.
- Firebase receives a device token and notification payload for push delivery.

Provider use is optional by environment and must be disclosed in the production privacy notice.

## Visibility

Official rankings, published tournaments, curated map guides, public transfer rumours, and active CRA sanctions are public surfaces. Private offers, private notes, team guides, security events, payment records, chats, and admin investigation details are authorization-scoped.

## Minors

Signup records a self-declared adult status. A minor account requires confirmation that parental/guardian consent exists. This is a product-level declaration, not an identity-verification service; legal review and a verifiable consent process are required before serving minors publicly.

## Retention and rights

The database preserves career and integrity history by design, but a formal retention schedule is not yet implemented. Production work must define retention for OTPs, security events, chats, push tokens, failed payments, evidence, and delivery details. User export, correction, account deletion/anonymization, consent withdrawal, and appeals should be implemented with legal guidance for the launch jurisdictions.

Delivery addresses and private competitive evidence are especially sensitive and should receive field-level encryption or external vaulting before public commerce use.
