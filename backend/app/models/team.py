import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Mode, TeamRole, OrgTier


class Organization(Base):
    """
    Optional parent structure above a Team. A Team is NOT required to
    belong to an Organization — solo squads are fully valid.
    An org can have multiple Teams underneath it, one per org_tier
    (T1 First Team, T2 Second Team, T3 Academy, T4 Development).
    """
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    teams: Mapped[list["Team"]] = relationship(back_populates="organization")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regions.id"), nullable=False)
    region: Mapped["Region"] = relationship(back_populates="teams")

    # Optional — a Team can exist with no Organization at all.
    organization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    organization: Mapped["Organization | None"] = relationship(back_populates="teams")
    org_tier: Mapped[OrgTier | None] = mapped_column(SAEnum(OrgTier), nullable=True)

    # Competitive tier is INDEPENDENT of org_tier — a T2 Second Team can
    # out-perform another org's T1 First Team on the real leaderboard.
    # Tracked separately per mode since a team's standing can differ MP vs BR.
    competitive_tier_mp: Mapped[int] = mapped_column(Integer, default=3)  # 1, 2, or 3
    competitive_tier_br: Mapped[int] = mapped_column(Integer, default=3)

    manager_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    manager: Mapped["User | None"] = relationship(foreign_keys=[manager_id])

    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    members: Mapped[list["TeamMember"]] = relationship(back_populates="team")


class TeamMember(Base):
    """
    Join table between User and Team, with a role (manager/player).
    A user's CURRENT team is derived from the row where is_active=True;
    old rows are kept (is_active=False) so a player's history persists
    across transfers/promotions — see PlayerTimelineEvent.
    """
    __tablename__ = "team_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[TeamRole] = mapped_column(SAEnum(TeamRole), default=TeamRole.PLAYER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    left_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    team: Mapped["Team"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="team_memberships")


class PlayerTimelineEvent(Base):
    """
    Auto-generated history log shown on a player's profile:
    'Promoted from Academy to First Team', 'Loaned to X for 2 months',
    'Signed new contract', 'Became free agent', etc.
    Personal competitive stats/ranking are NOT reset by any of these
    events — only the team_id attachment changes.
    """
    __tablename__ = "player_timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "promotion", "transfer", "loan", etc.
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    from_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    to_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
