from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import (
    PlayerContractStatus,
    RumourReliability,
    TransferOfferStatus,
    TransferOfferType,
)


class OfferTerms(BaseModel):
    transfer_fee_naira: int | None = Field(default=None, ge=0)
    fee_is_public: bool = True
    loan_fee_naira: int | None = Field(default=None, ge=0)
    loan_duration_days: int | None = Field(default=None, ge=7, le=730)
    loan_salary_payer: Literal["origin", "destination", "shared"] | None = None
    loan_option_to_buy: bool = False
    loan_recall_clause: bool = False
    proposed_salary_naira: int | None = Field(default=None, ge=0)
    proposed_contract_length_months: int | None = Field(default=12, ge=1, le=60)
    public_note: str | None = Field(default=None, max_length=500)
    private_note: str | None = Field(default=None, max_length=1000)


class OfferCreate(OfferTerms):
    player_id: uuid.UUID
    to_team_id: uuid.UUID
    offer_type: TransferOfferType
    expires_in_hours: int = Field(default=72, ge=1, le=720)

    @model_validator(mode="after")
    def validate_offer_type(self):
        if self.offer_type == TransferOfferType.LOAN and not self.loan_duration_days:
            raise ValueError("loan_duration_days is required for a loan offer")
        if self.offer_type != TransferOfferType.LOAN and any(
            value is not None for value in (self.loan_fee_naira, self.loan_duration_days, self.loan_salary_payer)
        ):
            raise ValueError("loan terms are only valid for loan offers")
        return self


class ClubDecision(OfferTerms):
    decision: Literal["approve", "reject", "counter"]
    note: str | None = Field(default=None, max_length=500)


class CounterDecision(BaseModel):
    accept: bool
    note: str | None = Field(default=None, max_length=500)


class PlayerDecision(BaseModel):
    accept: bool
    note: str | None = Field(default=None, max_length=500)


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    player_id: uuid.UUID
    from_team_id: uuid.UUID | None
    to_team_id: uuid.UUID
    created_by: uuid.UUID
    offer_type: TransferOfferType
    status: TransferOfferStatus
    transfer_fee_naira: int | None
    fee_is_public: bool
    loan_fee_naira: int | None
    loan_duration_days: int | None
    loan_salary_payer: str | None
    loan_option_to_buy: bool
    loan_recall_clause: bool
    proposed_salary_naira: int | None
    proposed_contract_length_months: int | None
    public_note: str | None
    private_note: str | None
    expires_at: datetime
    created_at: datetime
    resolved_at: datetime | None


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    player_id: uuid.UUID
    team_id: uuid.UUID
    parent_contract_id: uuid.UUID | None
    loan_return_team_id: uuid.UUID | None
    status: PlayerContractStatus
    start_date: date
    end_date: date | None
    salary_naira: int | None
    buyout_clause_naira: int | None
    is_active: bool


class WatchlistIn(BaseModel):
    player_id: uuid.UUID
    priority: int = Field(default=3, ge=1, le=5)
    note: str | None = Field(default=None, max_length=1000)


class RumourIn(BaseModel):
    player_id: uuid.UUID
    from_team_id: uuid.UUID | None = None
    linked_team_id: uuid.UUID | None = None
    headline: str = Field(min_length=5, max_length=200)
    summary: str = Field(min_length=10, max_length=5000)
    source_label: str | None = Field(default=None, max_length=100)
    reliability: RumourReliability = RumourReliability.LOW
    is_public: bool = False


class TransferWindowIn(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    season_id: uuid.UUID | None = None
    tournament_id: uuid.UUID | None = None
    registration_opens: datetime
    registration_closes: datetime
    roster_lock_date: datetime
    transfer_window_opens: datetime
    transfer_window_closes: datetime
    emergency_stand_in_allowed: bool = True
    late_registration_allowed: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if not self.registration_opens < self.registration_closes <= self.roster_lock_date:
            raise ValueError("registration dates must end on or before roster lock")
        if not self.transfer_window_opens < self.transfer_window_closes <= self.roster_lock_date:
            raise ValueError("the transfer window must close on or before roster lock")
        return self


class ContractListingIn(BaseModel):
    status: Literal["transfer_listed", "loan_listed", "under_contract"]
