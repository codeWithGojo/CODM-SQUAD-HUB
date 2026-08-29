from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.models.enums import (
    PlayerContractStatus,
    RumourReliability,
    TransferOfferStatus,
    TransferOfferType,
)


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (
        Index("contract_player_status_idx", "player_id", "status", "end_date"),
        Index(
            "uq_active_contract_per_player",
            "player_id",
            unique=True,
            postgresql_where=text("is_active"),
            sqlite_where=text("is_active = 1"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    parent_contract_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("contracts.id"), nullable=True)
    loan_return_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    status: Mapped[PlayerContractStatus] = mapped_column(
        SAEnum(PlayerContractStatus), default=PlayerContractStatus.UNDER_CONTRACT, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    salary_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    buyout_clause_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    buyout_clause_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    terms: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    signed_by_player_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signed_by_team_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TransferOffer(Base):
    __tablename__ = "transfer_offers"
    __table_args__ = (
        Index("transfer_offer_inbox_idx", "from_team_id", "status", "created_at"),
        Index("transfer_offer_player_status_idx", "player_id", "status", "expires_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    from_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    to_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    offer_type: Mapped[TransferOfferType] = mapped_column(SAEnum(TransferOfferType), nullable=False)
    status: Mapped[TransferOfferStatus] = mapped_column(
        SAEnum(TransferOfferStatus), default=TransferOfferStatus.PENDING_CLUB_REVIEW, nullable=False
    )
    transfer_fee_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee_is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    loan_fee_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loan_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loan_salary_payer: Mapped[str | None] = mapped_column(String(30), nullable=True)
    loan_option_to_buy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    loan_recall_clause: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    proposed_salary_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proposed_contract_length_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    public_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    private_note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    counters_offer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("transfer_offers.id"), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TransferOfferEvent(Base):
    __tablename__ = "transfer_offer_events"
    __table_args__ = (Index("transfer_event_offer_time_idx", "offer_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transfer_offers.id"), nullable=False)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TransferWatchlist(Base):
    __tablename__ = "transfer_watchlists"
    __table_args__ = (
        UniqueConstraint("team_id", "player_id", name="uq_transfer_watchlist_team_player"),
        Index("transfer_watchlist_team_idx", "team_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    added_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TransferRumour(Base):
    __tablename__ = "transfer_rumours"
    __table_args__ = (Index("transfer_rumour_public_idx", "is_public", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    from_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    linked_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    headline: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reliability: Mapped[RumourReliability] = mapped_column(
        SAEnum(RumourReliability), default=RumourReliability.LOW, nullable=False
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class MarketValueSnapshot(Base):
    __tablename__ = "market_value_snapshots"
    __table_args__ = (Index("market_value_player_time_idx", "player_id", "computed_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    estimated_value_naira: Mapped[int] = mapped_column(Integer, nullable=False)
    factors: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    trigger_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TransferWindow(Base):
    __tablename__ = "transfer_windows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    organizer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    season_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("seasons.id"), nullable=True)
    tournament_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tournaments.id"), nullable=True)
    registration_opens: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_closes: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    roster_lock_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    transfer_window_opens: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    transfer_window_closes: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    emergency_stand_in_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    late_registration_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
