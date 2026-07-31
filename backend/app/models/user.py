import uuid
from datetime import datetime, timedelta

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Mode


class Region(Base):
    """
    Nigeria, East Africa, etc. Kept as data (not a hardcoded enum) so new
    African regions can be added later without a schema change.
    """
    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # "Nigeria"
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)   # "NG"

    users: Mapped[list["User"]] = relationship(back_populates="region")
    teams: Mapped[list["Team"]] = relationship(back_populates="region")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    gamertag: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    preferred_mode: Mapped[Mode | None] = mapped_column(SAEnum(Mode), nullable=True)

    region_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("regions.id"), nullable=True)
    region: Mapped["Region"] = relationship(back_populates="users")

    # Age/consent — self-declared checkbox at signup, not independently verified.
    is_adult: Mapped[bool] = mapped_column(Boolean, default=True)
    parental_consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    banned_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # For push notifications (weekly review ready, scrim reminders, challenge updates)
    fcm_device_token: Mapped[str | None] = mapped_column(String(255), nullable=True)

    team_memberships: Mapped[list["TeamMember"]] = relationship(back_populates="user")


class OTPCode(Base):
    """
    Short-lived codes for phone-number login. A row is created on
    'request OTP', consumed (used=True) on successful 'verify OTP'.
    """
    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @staticmethod
    def new_expiry(minutes: int) -> datetime:
        return datetime.utcnow() + timedelta(minutes=minutes)
