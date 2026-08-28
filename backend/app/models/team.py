from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time import utcnow
from app.models.enums import OrgTier, TeamRole, VerificationStatus


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SAEnum(VerificationStatus), default=VerificationStatus.UNVERIFIED, nullable=False
    )
    reputation_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    teams: Mapped[list[Team]] = relationship(back_populates="organization")


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (
        UniqueConstraint("organization_id", "org_tier", "name", name="uq_org_roster_name"),
        CheckConstraint("competitive_tier_mp between 1 and 4", name="ck_team_mp_tier"),
        CheckConstraint("competitive_tier_br between 1 and 4", name="ck_team_br_tier"),
        Index("teams_region_active_idx", "region_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regions.id"), nullable=False, index=True)
    region: Mapped[Region] = relationship(back_populates="teams")
    organization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    organization: Mapped[Organization | None] = relationship(back_populates="teams")
    org_tier: Mapped[OrgTier | None] = mapped_column(SAEnum(OrgTier), nullable=True)
    primary_mode: Mapped[str | None] = mapped_column(String(10), nullable=True)
    competitive_tier_mp: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    competitive_tier_br: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    manager: Mapped[User | None] = relationship(foreign_keys=[manager_id])
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reputation_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    members: Mapped[list[TeamMember]] = relationship(back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (
        Index("team_members_team_active_idx", "team_id", "is_active"),
        Index("team_members_user_active_idx", "user_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[TeamRole] = mapped_column(SAEnum(TeamRole), default=TeamRole.PLAYER, nullable=False)
    in_game_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    team: Mapped[Team] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="team_memberships")


class PlayerTimelineEvent(Base):
    __tablename__ = "player_timeline_events"
    __table_args__ = (Index("timeline_user_created_idx", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    from_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    to_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import Region, User
