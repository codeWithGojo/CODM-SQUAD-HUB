from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import (
    BlacklistStatus,
    BlacklistSubjectType,
    DisputeStatus,
    Mode,
    RegistrationStatus,
    SanctionType,
    TournamentFormat,
    TournamentMatchStatus,
    TournamentStatus,
)


class ORMModel(BaseModel):
    model_config = {"from_attributes": True}


class TournamentCreateIn(BaseModel):
    name: str = Field(min_length=3, max_length=150)
    slug: str = Field(min_length=3, max_length=180, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    mode: Mode
    format: TournamentFormat
    tier: str = Field(default="community", max_length=30)
    season_id: uuid.UUID | None = None
    country_code: str | None = Field(default=None, max_length=10)
    region_code: str | None = Field(default=None, max_length=50)
    max_teams: int = Field(default=16, ge=2, le=256)
    min_roster_size: int = Field(default=5, ge=1, le=100)
    max_roster_size: int = Field(default=8, ge=1, le=100)
    ranking_weight: float = Field(default=1.0, ge=0.1, le=5.0)
    entry_fee_kobo: int = Field(default=0, ge=0)
    prize_pool_naira: int = Field(default=0, ge=0)
    rules: dict = Field(default_factory=dict)
    registration_opens_at: datetime | None = None
    registration_closes_at: datetime | None = None
    roster_lock_at: datetime | None = None
    starts_at: datetime
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def validate_timeline(self):
        if self.min_roster_size > self.max_roster_size:
            raise ValueError("min_roster_size cannot exceed max_roster_size")
        if self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        if self.registration_opens_at and self.registration_closes_at and self.registration_opens_at >= self.registration_closes_at:
            raise ValueError("registration_opens_at must be before registration_closes_at")
        if self.registration_closes_at and self.registration_closes_at >= self.starts_at:
            raise ValueError("registration must close before the tournament starts")
        if self.roster_lock_at and self.roster_lock_at >= self.starts_at:
            raise ValueError("roster_lock_at must be before the tournament starts")
        if self.registration_closes_at and self.roster_lock_at and self.roster_lock_at < self.registration_closes_at:
            raise ValueError("roster_lock_at cannot be before registration closes")
        return self


class TournamentUpdateIn(BaseModel):
    description: str | None = None
    status: TournamentStatus | None = None
    rules: dict | None = None
    broadcast_links: list[dict] | None = None
    registration_closes_at: datetime | None = None
    roster_lock_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class TournamentOut(ORMModel):
    id: uuid.UUID
    organizer_id: uuid.UUID
    season_id: uuid.UUID | None
    name: str
    slug: str
    description: str | None
    mode: Mode
    format: TournamentFormat
    tier: str
    status: TournamentStatus
    country_code: str | None
    region_code: str | None
    max_teams: int
    min_roster_size: int
    max_roster_size: int
    ranking_weight: float
    entry_fee_kobo: int
    prize_pool_naira: int
    rules: dict
    bracket: dict
    broadcast_links: list[dict]
    registration_opens_at: datetime | None
    registration_closes_at: datetime | None
    roster_lock_at: datetime | None
    starts_at: datetime
    ends_at: datetime | None
    published_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class RegistrationIn(BaseModel):
    team_id: uuid.UUID
    roster_user_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    stand_in_user_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)


class RegistrationReviewIn(BaseModel):
    status: RegistrationStatus
    seed: int | None = Field(default=None, ge=1)
    review_note: str | None = Field(default=None, max_length=500)


class RegistrationOut(ORMModel):
    id: uuid.UUID
    tournament_id: uuid.UUID
    team_id: uuid.UUID
    submitted_by: uuid.UUID
    roster_user_ids: list[str]
    stand_in_user_ids: list[str]
    status: RegistrationStatus
    seed: int | None
    review_note: str | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class GenerateBracketIn(BaseModel):
    reset_existing: bool = False


class MatchCreateIn(BaseModel):
    round_name: str = Field(min_length=1, max_length=80)
    bracket_position: int | None = Field(default=None, ge=1)
    group_name: str | None = Field(default=None, max_length=40)
    team_a_id: uuid.UUID | None = None
    team_b_id: uuid.UUID | None = None
    best_of: int = Field(default=5, ge=1, le=21)
    scheduled_at: datetime | None = None


class MatchReportIn(BaseModel):
    score_a: int = Field(ge=0, le=1000)
    score_b: int = Field(ge=0, le=1000)
    map_scores: list[dict] = Field(default_factory=list, max_length=21)
    proof_urls: list[str] = Field(default_factory=list, max_length=20)
    played_at: datetime | None = None


class HillRoleProfileIn(BaseModel):
    objective_pressure: int = Field(ge=0, le=100)
    trades: int = Field(ge=0, le=100)
    survival: int = Field(ge=0, le=100)
    kills: int = Field(ge=0, le=100)
    objective: int = Field(ge=0, le=100)
    consistency: int = Field(ge=0, le=100)


class HillOutputIn(BaseModel):
    map_name: str = Field(min_length=2, max_length=50)
    hill_labels: list[str] = Field(min_length=1, max_length=20)
    kills_by_hill: list[int] = Field(min_length=1, max_length=20)
    shared_scale: int = Field(default=12, ge=1, le=50)
    role_profile: HillRoleProfileIn | None = None

    @model_validator(mode="after")
    def validate_hills(self):
        if len(self.hill_labels) != len(self.kills_by_hill):
            raise ValueError("hill_labels and kills_by_hill must contain the same number of entries")
        if any(not label.strip() or len(label) > 20 for label in self.hill_labels):
            raise ValueError("hill labels must contain 1 to 20 characters")
        if any(value < 0 or value > self.shared_scale for value in self.kills_by_hill):
            raise ValueError("kills_by_hill values must fit within shared_scale")
        return self


class PlayerStatIn(BaseModel):
    user_id: uuid.UUID
    team_id: uuid.UUID
    kills: int = Field(default=0, ge=0)
    deaths: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    objective_score: float = Field(default=0, ge=0)
    damage: int = Field(default=0, ge=0)
    placement: int | None = Field(default=None, ge=1)
    is_mvp: bool = False
    metadata_json: dict = Field(default_factory=dict)
    hill_output: HillOutputIn | None = None

    @model_validator(mode="after")
    def validate_hill_total(self):
        if self.hill_output and sum(self.hill_output.kills_by_hill) > self.kills:
            raise ValueError("hill output kills cannot exceed the submitted match kill total")
        return self


class MatchOut(ORMModel):
    id: uuid.UUID
    tournament_id: uuid.UUID
    round_name: str
    bracket_position: int | None
    group_name: str | None
    team_a_id: uuid.UUID | None
    team_b_id: uuid.UUID | None
    best_of: int
    status: TournamentMatchStatus
    score_a: int | None
    score_b: int | None
    winner_team_id: uuid.UUID | None
    map_scores: list[dict]
    proof_urls: list[str]
    scheduled_at: datetime | None
    played_at: datetime | None
    verified_at: datetime | None


class DisputeIn(BaseModel):
    match_id: uuid.UUID | None = None
    filing_team_id: uuid.UUID | None = None
    against_team_id: uuid.UUID | None = None
    summary: str = Field(min_length=5, max_length=500)
    details: str = Field(min_length=10, max_length=5000)
    evidence_urls: list[str] = Field(default_factory=list, max_length=20)


class DisputeRulingIn(BaseModel):
    status: DisputeStatus
    ruling: str = Field(min_length=5, max_length=5000)


class BlacklistEntryIn(BaseModel):
    subject_type: BlacklistSubjectType
    subject_id: uuid.UUID
    subject_name_snapshot: str = Field(min_length=2, max_length=150)
    sanction_type: SanctionType
    scope: str = Field(default="platform", max_length=50)
    public_reason: str = Field(min_length=5, max_length=500)
    internal_notes: str | None = Field(default=None, max_length=5000)
    evidence_urls: list[str] = Field(default_factory=list, max_length=20)
    related_dispute_id: uuid.UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @model_validator(mode="after")
    def validate_sanction_window(self):
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class BlacklistEntryOut(ORMModel):
    id: uuid.UUID
    subject_type: BlacklistSubjectType
    subject_id: uuid.UUID
    subject_name_snapshot: str
    sanction_type: SanctionType
    status: BlacklistStatus
    scope: str
    public_reason: str
    starts_at: datetime
    ends_at: datetime | None
    created_at: datetime


class BlacklistAppealIn(BaseModel):
    statement: str = Field(min_length=20, max_length=5000)
    evidence_urls: list[str] = Field(default_factory=list, max_length=20)


class BlacklistAppealDecisionIn(BaseModel):
    status: DisputeStatus
    decision: str = Field(min_length=5, max_length=5000)
    revoke_sanction: bool = False


class BlacklistRevokeIn(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)
