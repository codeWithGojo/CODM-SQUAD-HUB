from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
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
    CampaignStatus,
    OrderStatus,
    PaymentPurpose,
    SubscriptionTier,
)
from app.models.user import User
from app.schemas.commerce import (
    CampaignIn,
    CampaignStatusIn,
    CheckoutOut,
    ContributionIn,
    MerchOrderIn,
    MerchProductIn,
    OrderStatusIn,
    SubscriptionCheckoutIn,
)
from app.services.payments import (
    MONTHLY_PLAN_PRICES_KOBO,
    initialize_payment,
    mark_payment_success,
    plan_price,
    release_order_stock,
    valid_paystack_signature,
    verify_with_paystack,
)
from app.services.permissions import require_org_permission, require_team_manager

router = APIRouter(prefix="/commerce", tags=["commerce"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])


def _checkout(row: PaymentTransaction, configured: bool) -> CheckoutOut:
    return CheckoutOut(
        transaction_id=row.id,
        reference=row.reference,
        amount_kobo=row.amount_kobo,
        status=row.status,
        checkout_url=row.checkout_url,
        provider_configured=configured,
    )


@router.get("/plans")
def plans():
    return {
        tier.value: {
            "monthly_kobo": MONTHLY_PLAN_PRICES_KOBO[tier],
            "annual_kobo": MONTHLY_PLAN_PRICES_KOBO[tier] * 10,
            "team_priced": True,
        }
        for tier in SubscriptionTier
    }


@router.post("/subscriptions/checkout", response_model=CheckoutOut, status_code=status.HTTP_201_CREATED)
def subscription_checkout(
    payload: SubscriptionCheckoutIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, payload.team_id, current_user)
    if payload.tier == SubscriptionTier.FREE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The free tier does not require checkout.")
    transaction, configured = initialize_payment(
        db,
        user_id=current_user.id,
        email=payload.email,
        purpose=PaymentPurpose.SUBSCRIPTION,
        amount_kobo=plan_price(payload.tier, payload.billing_cycle),
        target_type="team",
        target_id=payload.team_id,
        metadata={"tier": payload.tier.value, "billing_cycle": payload.billing_cycle.value},
    )
    db.commit()
    db.refresh(transaction)
    return _checkout(transaction, configured)


@router.get("/subscriptions/teams/{team_id}")
def team_subscription(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, team_id, current_user)
    row = db.query(TeamSubscription).filter_by(team_id=team_id).first()
    return row or {"team_id": team_id, "tier": SubscriptionTier.FREE.value, "is_active": True}


@router.delete("/subscriptions/teams/{team_id}")
def cancel_team_subscription(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, team_id, current_user)
    row = db.query(TeamSubscription).filter_by(team_id=team_id).first()
    if not row:
        return {"team_id": team_id, "tier": SubscriptionTier.FREE.value, "is_active": True}
    row.tier = SubscriptionTier.FREE
    row.is_active = False
    row.cancelled_at = utcnow()
    row.paystack_subscription_code = None
    db.commit()
    db.refresh(row)
    return row


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
def create_campaign(
    payload: CampaignIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_permission(db, payload.organization_id, current_user, "finance.manage")
    values = payload.model_dump()
    values["status"] = CampaignStatus.DRAFT
    row = CrowdfundingCampaign(created_by=current_user.id, **values)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/campaigns/{campaign_id}")
def update_campaign_status(
    campaign_id: uuid.UUID,
    payload: CampaignStatusIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(CrowdfundingCampaign, campaign_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    require_org_permission(db, row.organization_id, current_user, "finance.manage")
    allowed = {
        CampaignStatus.DRAFT: {CampaignStatus.ACTIVE, CampaignStatus.CANCELLED},
        CampaignStatus.ACTIVE: {CampaignStatus.CLOSED, CampaignStatus.CANCELLED},
        CampaignStatus.FUNDED: {CampaignStatus.CLOSED},
        CampaignStatus.CLOSED: set(),
        CampaignStatus.CANCELLED: set(),
    }
    if payload.status not in allowed[row.status]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid campaign status transition.")
    row.status = payload.status
    db.commit()
    db.refresh(row)
    return row


@router.get("/campaigns")
def list_campaigns(
    organization_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(CrowdfundingCampaign).filter(CrowdfundingCampaign.status.in_([CampaignStatus.ACTIVE, CampaignStatus.FUNDED]))
    if organization_id:
        query = query.filter(CrowdfundingCampaign.organization_id == organization_id)
    return query.order_by(CrowdfundingCampaign.created_at.desc()).limit(limit).all()


@router.post("/campaigns/{campaign_id}/contributions", response_model=CheckoutOut, status_code=status.HTTP_201_CREATED)
def contribute(
    campaign_id: uuid.UUID,
    payload: ContributionIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = db.get(CrowdfundingCampaign, campaign_id)
    if not campaign or campaign.status != CampaignStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Campaign is not accepting contributions.")
    if campaign.ends_at and as_utc(campaign.ends_at) <= utcnow():
        campaign.status = CampaignStatus.CLOSED
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Campaign has ended.")
    contribution = CampaignContribution(
        campaign_id=campaign.id,
        contributor_user_id=current_user.id,
        amount_kobo=payload.amount_kobo,
        message=payload.message,
        anonymous=payload.anonymous,
    )
    db.add(contribution)
    db.flush()
    transaction, configured = initialize_payment(
        db,
        user_id=current_user.id,
        email=payload.email,
        purpose=PaymentPurpose.CROWDFUNDING,
        amount_kobo=payload.amount_kobo,
        target_type="campaign",
        target_id=campaign.id,
        metadata={"contribution_id": str(contribution.id)},
    )
    contribution.payment_transaction_id = transaction.id
    db.commit()
    db.refresh(transaction)
    return _checkout(transaction, configured)


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: MerchProductIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_permission(db, payload.organization_id, current_user, "store.manage")
    row = MerchProduct(created_by=current_user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/products")
def list_products(
    organization_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return db.query(MerchProduct).filter_by(organization_id=organization_id, is_active=True).order_by(MerchProduct.created_at.desc()).limit(limit).all()


@router.post("/orders", response_model=CheckoutOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: MerchOrderIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product_ids = list({item.product_id for item in payload.items})
    products = {
        row.id: row
        for row in db.query(MerchProduct)
        .filter(MerchProduct.id.in_(product_ids), MerchProduct.organization_id == payload.organization_id, MerchProduct.is_active.is_(True))
        .with_for_update()
        .all()
    }
    if len(products) != len(product_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more products are unavailable.")
    total = 0
    for item in payload.items:
        product = products[item.product_id]
        if product.stock_quantity is not None and product.stock_quantity < item.quantity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Insufficient stock for {product.name}.")
        total += product.price_kobo * item.quantity
    for item in payload.items:
        product = products[item.product_id]
        if product.stock_quantity is not None:
            product.stock_quantity -= item.quantity
    order = MerchOrder(
        organization_id=payload.organization_id,
        buyer_user_id=current_user.id,
        total_kobo=total,
        delivery_details=payload.delivery_details,
    )
    db.add(order)
    db.flush()
    for item in payload.items:
        product = products[item.product_id]
        db.add(
            MerchOrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                unit_price_kobo=product.price_kobo,
                variant_key=item.variant_key,
                variant_snapshot=item.variant_snapshot,
            )
        )
    transaction, configured = initialize_payment(
        db,
        user_id=current_user.id,
        email=payload.email,
        purpose=PaymentPurpose.MERCH,
        amount_kobo=total,
        target_type="merch_order",
        target_id=order.id,
        metadata={"organization_id": str(payload.organization_id)},
    )
    order.payment_transaction_id = transaction.id
    db.commit()
    db.refresh(transaction)
    return _checkout(transaction, configured)


@router.get("/orders")
def list_store_orders(
    organization_id: uuid.UUID,
    order_status: OrderStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_permission(db, organization_id, current_user, "store.manage")
    query = db.query(MerchOrder).filter(MerchOrder.organization_id == organization_id)
    if order_status:
        query = query.filter(MerchOrder.status == order_status)
    return query.order_by(MerchOrder.created_at.desc()).limit(limit).all()


@router.get("/orders/me")
def my_orders(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(MerchOrder).filter_by(buyer_user_id=current_user.id).order_by(MerchOrder.created_at.desc()).limit(limit).all()


@router.get("/orders/{order_id}")
def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.get(MerchOrder, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if order.buyer_user_id != current_user.id and not current_user.is_platform_admin:
        require_org_permission(db, order.organization_id, current_user, "store.manage")
    items = db.query(MerchOrderItem).filter_by(order_id=order.id).all()
    return {"order": order, "items": items}


@router.patch("/orders/{order_id}")
def update_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.get(MerchOrder, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    require_org_permission(db, order.organization_id, current_user, "store.manage")
    if payload.status == OrderStatus.PAID:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Paid status can only come from a verified payment.")
    allowed = {
        OrderStatus.PENDING_PAYMENT: {OrderStatus.CANCELLED},
        OrderStatus.PAID: {OrderStatus.PROCESSING},
        OrderStatus.PROCESSING: {OrderStatus.SHIPPED},
        OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
        OrderStatus.DELIVERED: set(),
        OrderStatus.CANCELLED: set(),
    }
    if payload.status not in allowed[order.status]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid order status transition.")
    if payload.status == OrderStatus.CANCELLED and order.status == OrderStatus.PENDING_PAYMENT:
        release_order_stock(db, order)
    order.status = payload.status
    order.fulfilment_reference = payload.fulfilment_reference
    db.commit()
    db.refresh(order)
    return order


@payments_router.get("/me")
def my_payments(
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(PaymentTransaction).filter_by(user_id=current_user.id).order_by(PaymentTransaction.created_at.desc()).limit(limit).all()


@payments_router.post("/{reference}/verify")
def verify_payment(
    reference: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(PaymentTransaction).filter_by(reference=reference).first()
    if not existing or (existing.user_id != current_user.id and not current_user.is_platform_admin):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")
    row = verify_with_paystack(db, reference)
    db.commit()
    db.refresh(row)
    return row


@payments_router.post("/paystack/webhook", status_code=status.HTTP_200_OK)
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    if not valid_paystack_signature(raw, request.headers.get("x-paystack-signature")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature.")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.") from exc
    event = payload.get("event")
    data = payload.get("data") or {}
    if event == "charge.success":
        try:
            row = mark_payment_success(db, reference=str(data.get("reference", "")), provider_data=data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        db.commit()
        return {"received": True, "matched": bool(row)}
    return {"received": True, "ignored": event}
