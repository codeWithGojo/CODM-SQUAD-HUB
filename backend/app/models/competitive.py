import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Mode, MatchResult, ChallengeStatus, ScrimStatus


class OfficialTeamResult(Base):
    """
    THE source of truth for team leaderboards. Only a team's manager can
    submit these — this is the deliberate separation from PlayerMatchLog
    that keeps individual players from being able to inflate the public
    leaderboard themselves.
    """
    __tablename__ = "official_team_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    opponent_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    challenge_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("challenges.id"), nullable=True)

    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    result: Mapped[MatchResult] = mapped_column(SAEnum(MatchResult), nullable=False)
    score_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    submitted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)  # the manager
    # Screenshot proof — required, used to resolve disputes.
    proof_screenshot_url: Mapped[str] = mapped_column(String(255), nullable=False)

    is_disputed: Mapped[bool] = mapped_column(Boolean, default=False)
    dispute_resolved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # a Tournament Organizer

    played_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Challenge(Base):
    """A team formally challenging another team, same-region or cross-region."""
    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenger_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    challenged_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    status: Mapped[ChallengeStatus] = mapped_column(SAEnum(ChallengeStatus), default=ChallengeStatus.PENDING)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Scrim(Base):
    """Practice matches — not official, but drives push-notification reminders."""
    __tablename__ = "scrims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    opponent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[ScrimStatus] = mapped_column(SAEnum(ScrimStatus), default=ScrimStatus.UPCOMING)
    reminder_1h_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_15m_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PlayerMatchLog(Base):
    """
    A PLAYER's own self-reported match log. Personal only — never
    feeds the official team leaderboard. Feeds the AI weekly review.
    """
    __tablename__ = "player_match_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    result: Mapped[MatchResult | None] = mapped_column(SAEnum(MatchResult), nullable=True)
    kills: Mapped[int | None] = mapped_column(nullable=True)
    deaths: Mapped[int | None] = mapped_column(nullable=True)
    # Quick-tap tags — see app/core/tags.py for the fixed vocabulary shown in the UI.
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    note: Mapped[str | None] = mapped_column(String(150), nullable=True)
    played_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
