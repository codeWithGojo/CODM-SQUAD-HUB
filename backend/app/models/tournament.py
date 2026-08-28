from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.models.enums import Mode, RegistrationStatus, TournamentFormat, TournamentMatchStatus, TournamentStatus


class Tournament(Base):
    __tablename__ = "tournaments"
    __table_args__ = (
        CheckConstraint("max_teams >= 2", name="ck_tournament_minimum_size"),
        CheckConstraint("ranking_weight >= 0.1 and ranking_weight <= 5.0", name="ck_tournament_weight"),
        Index("tournament_status_start_idx", "status", "starts_at"),
        Index("tournament_scope_mode_idx", "country_code", "region_code", "mode"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    season_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("seasons.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    format: Mapped[TournamentFormat] = mapped_column(SAEnum(TournamentFormat), nullable=False)
    tier: Mapped[str] = mapped_column(String(30), default="community", nullable=False)
    status: Mapped[TournamentStatus] = mapped_column(
        SAEnum(TournamentStatus), default=TournamentStatus.DRAFT, nullable=False
    )
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    max_teams: Mapped[int] = mapped_column(Integer, default=16, nullable=False)
    min_roster_size: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_roster_size: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    ranking_weight: Mapped[float] = mapped_column(Numeric(4, 2), default=1.0, nullable=False)
    entry_fee_kobo: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prize_pool_naira: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rules: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    bracket: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    broadcast_links: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    registration_opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    registration_closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    roster_lock_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class TournamentRegistration(Base):
    __tablename__ = "tournament_registrations"
    __table_args__ = (
        UniqueConstraint("tournament_id", "team_id", name="uq_tournament_team_registration"),
        Index("registration_tournament_status_idx", "tournament_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    submitted_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    roster_user_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    stand_in_user_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[RegistrationStatus] = mapped_column(
        SAEnum(RegistrationStatus), default=RegistrationStatus.PENDING, nullable=False
    )
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TournamentMatch(Base):
    __tablename__ = "tournament_matches"
    __table_args__ = (
        CheckConstraint("team_a_id is null or team_b_id is null or team_a_id <> team_b_id", name="ck_match_different_teams"),
        Index("tournament_match_schedule_idx", "tournament_id", "scheduled_at"),
        Index("tournament_match_status_idx", "status", "scheduled_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    round_name: Mapped[str] = mapped_column(String(80), nullable=False)
    bracket_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(40), nullable=True)
    team_a_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    team_b_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    best_of: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    status: Mapped[TournamentMatchStatus] = mapped_column(
        SAEnum(TournamentMatchStatus), default=TournamentMatchStatus.SCHEDULED, nullable=False
    )
    score_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_b: Mapped[int | None] = mapped_column(Integer, nullable=True)
    winner_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    map_scores: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    proof_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    reported_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TournamentPlayerStat(Base):
    __tablename__ = "tournament_player_stats"
    __table_args__ = (
        UniqueConstraint("match_id", "user_id", name="uq_match_player_stat"),
        Index("player_stat_user_idx", "user_id", "match_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tournament_matches.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    kills: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deaths: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assists: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    objective_score: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    damage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    placement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_mvp: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TournamentStanding(Base):
    __tablename__ = "tournament_standings"
    __table_args__ = (UniqueConstraint("tournament_id", "team_id", name="uq_tournament_standing"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    draws: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_for: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_against: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    placement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
