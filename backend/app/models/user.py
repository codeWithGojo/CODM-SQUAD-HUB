from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from app.models.enums import CareerStatus, Mode, VerificationStatus


def new_shid() -> str:
    return f"SH-{uuid.uuid4().hex[:10].upper()}"


class Region(Base):
    """Country and African regional-zone metadata used by ranking scopes."""

    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    zone: Mapped[str] = mapped_column(String(50), nullable=False, default="Unassigned")

    users: Mapped[list[User]] = relationship(back_populates="region")
    teams: Mapped[list[Team]] = relationship(back_populates="region")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("users_region_active_idx", "region_id", "career_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shid: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, default=new_shid)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    gamertag: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    preferred_mode: Mapped[Mode | None] = mapped_column(SAEnum(Mode), nullable=True)

    region_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("regions.id"), nullable=True, index=True)
    region: Mapped[Region | None] = relationship(back_populates="users")

    is_adult: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parental_consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus), default=VerificationStatus.UNVERIFIED, nullable=False
    )
    career_status: Mapped[CareerStatus] = mapped_column(
        SAEnum(CareerStatus), default=CareerStatus.ACTIVE, nullable=False
    )
    is_platform_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reputation_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ban_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    banned_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    last_known_ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    device_fingerprint_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    fcm_device_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    team_memberships: Mapped[list[TeamMember]] = relationship(back_populates="user")


class OTPCode(Base):
    __tablename__ = "otp_codes"
    __table_args__ = (Index("otp_phone_created_idx", "phone", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    @staticmethod
    def new_expiry(minutes: int) -> datetime:
        return utcnow() + timedelta(minutes=minutes)


class AccountSecurityEvent(Base):
    """Restricted audit data for ban-evasion and account-compromise investigations."""

    __tablename__ = "account_security_events"
    __table_args__ = (
        Index("security_user_created_idx", "user_id", "created_at"),
        Index("security_ip_hash_idx", "ip_hash"),
        Index("security_device_hash_idx", "device_fingerprint_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    phone_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_fingerprint_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.team import Team, TeamMember
