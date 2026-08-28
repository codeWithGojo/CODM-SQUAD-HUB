from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import as_utc, utcnow
from app.models.commerce import (
    CampaignContribution,
    CrowdfundingCampaign,
    MerchOrder,
    MerchOrderItem,
    MerchProduct,
    PaymentTransaction,
    TeamSubscription,
)
from app.models.enums import (
    BillingCycle,
    CampaignStatus,
    OrderStatus,
    PaymentPurpose,
    PaymentStatus,
    SubscriptionTier,
)


MONTHLY_PLAN_PRICES_KOBO = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.STARTER: 150_000,
    SubscriptionTier.PRO: 400_000,
    SubscriptionTier.ELITE: 1_000_000,
}


def plan_price(tier: SubscriptionTier, cycle: BillingCycle) -> int:
    monthly = MONTHLY_PLAN_PRICES_KOBO[tier]
    return monthly if cycle == BillingCycle.MONTHLY else monthly * 10


def create_reference() -> str:
    return f"SH-{uuid.uuid4().hex[:20].upper()}"


def initialize_payment(
    db: Session,
    *,
    user_id: uuid.UUID,
    email: str,
    purpose: PaymentPurpose,
    amount_kobo: int,
    target_type: str,
    target_id: uuid.UUID,
    metadata: dict | None = None,
) -> tuple[PaymentTransaction, bool]:
    if amount_kobo < 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount must be at least ₦1.")
    transaction = PaymentTransaction(
        reference=create_reference(),
        user_id=user_id,
        purpose=purpose,
        amount_kobo=amount_kobo,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata or {},
    )
    db.add(transaction)
    db.flush()
    if not settings.paystack_secret_key:
        return transaction, False

    response = httpx.post(
        "https://api.paystack.co/transaction/initialize",
        headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
        json={
            "email": email,
            "amount": amount_kobo,
            "currency": "NGN",
            "reference": transaction.reference,
            "callback_url": settings.paystack_callback_url or None,
            "metadata": {"purpose": purpose.value, "target_type": target_type, "target_id": str(target_id), **(metadata or {})},
        },
        timeout=20.0,
    )
    response.raise_for_status()
    data = response.json().get("data") or {}
    transaction.provider_reference = data.get("access_code")
    transaction.checkout_url = data.get("authorization_url")
    transaction.status = PaymentStatus.PENDING
    return transaction, True


def valid_paystack_signature(raw_body: bytes, signature: str | None) -> bool:
    if not signature or not settings.paystack_secret_key:
        return False
    expected = hmac.new(settings.paystack_secret_key.encode(), raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature)


def mark_payment_success(db: Session, *, reference: str, provider_data: dict) -> PaymentTransaction | None:
    transaction = db.query(PaymentTransaction).filter_by(reference=reference).with_for_update().first()
    if not transaction:
        return None
    if transaction.status == PaymentStatus.SUCCESS:
        return transaction
    amount = provider_data.get("amount")
    currency = provider_data.get("currency")
    if amount != transaction.amount_kobo or currency != transaction.currency:
        raise ValueError("Paystack amount or currency does not match the initialized transaction")
    transaction.status = PaymentStatus.SUCCESS
    transaction.paid_at = utcnow()
    transaction.provider_reference = str(provider_data.get("id") or provider_data.get("reference") or transaction.reference)
    _apply_entitlement(db, transaction)
    return transaction


def _apply_entitlement(db: Session, transaction: PaymentTransaction) -> None:
    if transaction.purpose == PaymentPurpose.SUBSCRIPTION:
        tier = SubscriptionTier(transaction.metadata_json["tier"])
        cycle = BillingCycle(transaction.metadata_json["billing_cycle"])
        row = db.query(TeamSubscription).filter_by(team_id=transaction.target_id).first()
        if not row:
            row = TeamSubscription(team_id=transaction.target_id)
            db.add(row)
        row.tier = tier
        row.billing_cycle = cycle
        row.is_active = True
        row.cancelled_at = None
        now = utcnow()
        period_start = max(now, as_utc(row.current_period_ends_at)) if row.current_period_ends_at else now
        row.current_period_ends_at = period_start + timedelta(days=365 if cycle == BillingCycle.ANNUAL else 30)
    elif transaction.purpose == PaymentPurpose.CROWDFUNDING:
        contribution = db.query(CampaignContribution).filter_by(payment_transaction_id=transaction.id).first()
        if contribution and contribution.confirmed_at is None:
            contribution.confirmed_at = utcnow()
            campaign = db.get(CrowdfundingCampaign, contribution.campaign_id)
            campaign.raised_kobo += contribution.amount_kobo
            if campaign.raised_kobo >= campaign.target_kobo:
                campaign.status = CampaignStatus.FUNDED
    elif transaction.purpose == PaymentPurpose.MERCH:
        order = db.query(MerchOrder).filter_by(payment_transaction_id=transaction.id).first()
        if order:
            order.status = OrderStatus.PAID


def release_order_stock(db: Session, order: MerchOrder) -> None:
    if not order.stock_reserved:
        return
    items = db.query(MerchOrderItem).filter_by(order_id=order.id).all()
    product_ids = [item.product_id for item in items]
    products = {
        row.id: row
        for row in db.query(MerchProduct).filter(MerchProduct.id.in_(product_ids)).with_for_update().all()
    }
    for item in items:
        product = products.get(item.product_id)
        if product and product.stock_quantity is not None:
            product.stock_quantity += item.quantity
    order.stock_reserved = False


def verify_with_paystack(db: Session, reference: str) -> PaymentTransaction:
    transaction = db.query(PaymentTransaction).filter_by(reference=reference).first()
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    if transaction.status == PaymentStatus.SUCCESS:
        return transaction
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Paystack is not configured.")
    response = httpx.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json().get("data") or {}
    if payload.get("status") == "success":
        mark_payment_success(db, reference=reference, provider_data=payload)
    elif payload.get("status") in {"failed", "abandoned"}:
        transaction.status = PaymentStatus(payload["status"])
        if transaction.purpose == PaymentPurpose.MERCH:
            order = db.query(MerchOrder).filter_by(payment_transaction_id=transaction.id).first()
            if order:
                release_order_stock(db, order)
                order.status = OrderStatus.CANCELLED
    return transaction
