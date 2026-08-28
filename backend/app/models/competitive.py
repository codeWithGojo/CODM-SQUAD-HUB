from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.models.enums import ChallengeStatus, MatchResult, Mode, ScrimStatus


class OfficialTeamResult(Base):
    """Verified competitive ledger. This, not self-reported player logs, drives rankings."""

    __tablename__ = "official_team_results"
    __table_args__ = (
        UniqueConstraint("tournament_match_id", "team_id", name="uq_official_result_match_team"),
        UniqueConstraint("challenge_id", "team_id", name="uq_official_result_challenge_team"),
        Index("official_result_team_mode_played_idx", "team_id", "mode", "played_at"),
        Index("official_result_verified_played_idx", "is_verified", "played_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    opponent_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    challenge_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("challenges.id"), nullable=True)
    tournament_match_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tournament_matches.id"), nullable=True)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    result: Mapped[MatchResult] = mapped_column(SAEnum(MatchResult), nullable=False)
    score_for: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_against: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    submitted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    proof_screenshot_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_disputed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Challenge(Base):
    __tablename__ = "challenges"
    __table_args__ = (Index("challenge_team_status_idx", "challenger_team_id", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenger_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    challenged_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    format: Mapped[str] = mapped_column(String(50), default="BO5", nullable=False)
    status: Mapped[ChallengeStatus] = mapped_column(
        SAEnum(ChallengeStatus), default=ChallengeStatus.PENDING, nullable=False
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score_challenger: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_challenged: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    proof_screenshot_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    result_reported_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    result_reported_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    result_confirmed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Scrim(Base):
    __tablename__ = "scrims"
    __table_args__ = (Index("scrim_schedule_status_idx", "scheduled_at", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    opponent_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    opponent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    format: Mapped[str] = mapped_column(String(50), default="BO5", nullable=False)
    maps: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    requirements: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[ScrimStatus] = mapped_column(SAEnum(ScrimStatus), default=ScrimStatus.UPCOMING, nullable=False)
    reminder_1h_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reminder_15m_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class PlayerMatchLog(Base):
    """Private player log used for coaching; never counted as an official ranking result."""

    __tablename__ = "player_match_logs"
    __table_args__ = (Index("player_match_user_played_idx", "user_id", "played_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    game_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    map_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    result: Mapped[MatchResult | None] = mapped_column(SAEnum(MatchResult), nullable=True)
    kills: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deaths: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    damage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    objective_score: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
