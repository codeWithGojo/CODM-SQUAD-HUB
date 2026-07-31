import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, ForeignKey, Enum as SAEnum, Integer, JSON, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PlayerContractStatus, TransferOfferType, TransferOfferStatus


class Contract(Base):
    """
    A player's current (or past — kept for history) contract with a team.
    Only one contract can be ACTIVE per player at a time.
    """
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)

    status: Mapped[PlayerContractStatus] = mapped_column(SAEnum(PlayerContractStatus), default=PlayerContractStatus.UNDER_CONTRACT)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Salary is intentionally never exposed publicly (see visibility rules).
    salary_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    buyout_clause_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    buyout_clause_public: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TransferOffer(Base):
    """
    One offer in the transfer workflow:
    Club A creates -> Club B accepts/rejects/counters -> Player accepts/rejects
    -> Contract generated -> transfer executes.
    """
    __tablename__ = "transfer_offers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    from_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)  # null if player is a free agent
    to_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)

    offer_type: Mapped[TransferOfferType] = mapped_column(SAEnum(TransferOfferType), nullable=False)
    status: Mapped[TransferOfferStatus] = mapped_column(SAEnum(TransferOfferStatus), default=TransferOfferStatus.PENDING_CLUB_REVIEW)

    # Permanent transfer terms
    transfer_fee_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee_is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    # Loan-specific terms
    loan_fee_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loan_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loan_salary_payer: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "parent_club" / "borrowing_club" / "shared"
    loan_option_to_buy: Mapped[bool] = mapped_column(Boolean, default=False)
    loan_recall_clause: Mapped[bool] = mapped_column(Boolean, default=False)

    # Player personal terms (set once it reaches player review stage)
    proposed_salary_naira: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proposed_contract_length_months: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Counter-offer chain — points back to the offer it's countering.
    counters_offer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("transfer_offers.id"), nullable=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class MarketValueSnapshot(Base):
    """
    Periodic estimate of a player's market value — an estimate only,
    doesn't force any deal. Recomputed on trigger events (tournament win,
    promotion/demotion, org change, ranking shift) rather than a fixed
    schedule, and we keep history so we can show a value-over-time graph.
    """
    __tablename__ = "market_value_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    estimated_value_naira: Mapped[int] = mapped_column(Integer, nullable=False)
    # What drove this number — kept for transparency/debugging, not shown raw to users.
    factors: Mapped[dict] = mapped_column(JSON, default=dict)
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TransferWindow(Base):
    """
    Organizer-configurable windows that gate when transfers/roster edits
    are allowed. Applies per tournament/season — a Tournament Organizer
    (any user who has applied for that role) sets these.
    """
    __tablename__ = "transfer_windows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "2026 Nigeria Season 1"
    organizer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    registration_opens: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    registration_closes: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    roster_lock_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    transfer_window_opens: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    transfer_window_closes: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    emergency_stand_in_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    late_registration_allowed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
