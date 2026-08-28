# Payment and Commerce System

Paystack is the implemented payment provider. All provider-facing amounts are integer kobo and all initialized transactions use NGN.

## Team premium

Premium is prepaid rather than an automatically recurring Paystack subscription.

| Tier | Monthly | Annual |
|---|---:|---:|
| Free | N0 | N0 |
| Starter | N1,500 | N15,000 |
| Pro | N4,000 | N40,000 |
| Elite | N10,000 | N100,000 |

Annual checkout charges ten monthly periods. A verified renewal extends from the later of today or the current paid-through date, preserving unused time. Cancellation downgrades the stored plan and prevents the application from treating it as active; there is no automatic debit mandate in this version.

## Checkout and verification

1. The backend creates a unique `PaymentTransaction` with the expected amount, purpose, target, user, and metadata.
2. If Paystack is configured, it initializes checkout and returns the hosted authorization URL.
3. The client can verify the reference, while Paystack can send `charge.success` to `/api/v1/payments/paystack/webhook`.
4. Webhooks require a SHA-512 HMAC signature generated from the exact raw request body.
5. The backend compares the returned currency and amount to the initialized transaction before applying an entitlement.
6. Repeated success events are idempotent.

## Crowdfunding

Organization finance staff create a draft campaign and explicitly activate it. Contributions are counted only after verified payment. Reaching the target marks the campaign funded; expired campaigns stop accepting contributions.

## Merchandise

Store staff create products with optional finite stock. Checkout locks product rows, validates every line, snapshots price/variant details, and reserves stock before initializing payment. A failed, abandoned, or manager-cancelled pending order releases the reservation exactly once. Buyers can view their orders; authorized store staff can list and advance fulfillment through paid to processing to shipped to delivered.

## Operational requirements

- Set `PAYSTACK_SECRET_KEY`, `PAYSTACK_PUBLIC_KEY`, and the callback URL.
- Register the signed webhook URL over HTTPS.
- Test successful, failed, abandoned, duplicate, wrong-amount, and wrong-currency events in Paystack's sandbox.
- Add a scheduled expiry/reconciliation job for long-abandoned checkouts before launch.
- Keep fulfillment and refund actions auditable; refunds are modeled but no refund-issuing endpoint is included yet.

Tournament-entry payment is reserved in the data model but is not exposed as a checkout route in this release.
