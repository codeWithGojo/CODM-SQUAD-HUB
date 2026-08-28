from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import BillingCycle, CampaignStatus, OrderStatus, PaymentStatus, SubscriptionTier


class CheckoutOut(BaseModel):
    transaction_id: uuid.UUID
    reference: str
    amount_kobo: int
    status: PaymentStatus
    checkout_url: str | None
    provider_configured: bool


class SubscriptionCheckoutIn(BaseModel):
    team_id: uuid.UUID
    tier: SubscriptionTier
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    email: str = Field(min_length=5, max_length=255)


class CampaignIn(BaseModel):
    organization_id: uuid.UUID
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=20, max_length=5000)
    target_kobo: int = Field(ge=100_000)
    cover_image_url: str | None = Field(default=None, max_length=500)
    ends_at: datetime | None = None
    status: CampaignStatus = CampaignStatus.DRAFT

    @model_validator(mode="after")
    def future_end(self):
        if self.ends_at and self.ends_at <= datetime.now(self.ends_at.tzinfo):
            raise ValueError("ends_at must be in the future")
        return self


class CampaignStatusIn(BaseModel):
    status: CampaignStatus


class ContributionIn(BaseModel):
    amount_kobo: int = Field(ge=10_000)
    email: str = Field(min_length=5, max_length=255)
    message: str | None = Field(default=None, max_length=500)
    anonymous: bool = False


class MerchProductIn(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=5000)
    price_kobo: int = Field(ge=10_000)
    image_urls: list[str] = Field(default_factory=list, max_length=10)
    variants: list[dict] = Field(default_factory=list, max_length=100)
    stock_quantity: int | None = Field(default=None, ge=0)
    external_fulfilment_url: str | None = Field(default=None, max_length=1000)


class OrderItemIn(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, le=100)
    variant_key: str = Field(default="default", max_length=200)
    variant_snapshot: dict = Field(default_factory=dict)


class MerchOrderIn(BaseModel):
    organization_id: uuid.UUID
    email: str = Field(min_length=5, max_length=255)
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)
    delivery_details: dict

    @model_validator(mode="after")
    def unique_lines(self):
        keys = [(item.product_id, item.variant_key) for item in self.items]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate product variants must be combined into one order line")
        return self


class OrderStatusIn(BaseModel):
    status: OrderStatus
    fulfilment_reference: str | None = Field(default=None, max_length=150)
