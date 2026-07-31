import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import Mode, SubscriptionTier


class MapGuide(Base):
    """
    Team-private reference content: one PDF + one YouTube-linked video
    per slot. NOT player-uploaded match replays (self-hosting video was
    priced out as too expensive). Up to 4 freeform-named slots per
    team, per map, per mode — e.g. "Attack A", "Passive BR rotations".
    """
    __tablename__ = "map_guides"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)  # private to this team
    map_name: Mapped[str] = mapped_column(String(50), nullable=False)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-4
    custom_title: Mapped[str] = mapped_column(String(50), nullable=False)  # freeform, manager-chosen
    pdf_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    """
    Team-level (not per-player) naira subscription. AI review cadence
    is driven off `tier` — e.g. 7/7 days for pro/elite, 2/7 for starter.
    """
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False, unique=True)
    tier: Mapped[SubscriptionTier] = mapped_column(SAEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    renews_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)


class AccountReport(Base):
    """
    Community-driven ban-evasion / misconduct reporting — the deliberately
    simple approach (no device fingerprinting or ID linking): the scene
    is small enough that players/managers recognize and flag bad actors.
    """
    __tablename__ = "account_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reported_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    reported_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    reviewed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
