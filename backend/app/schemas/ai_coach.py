from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import AIReviewStatus, MatchResult, Mode, TrainingAssignmentStatus


class PlayerMatchLogIn(BaseModel):
    team_id: uuid.UUID | None = None
    mode: Mode
    game_mode: str | None = Field(default=None, max_length=50)
    map_name: str | None = Field(default=None, max_length=50)
    result: MatchResult | None = None
    kills: int = Field(default=0, ge=0, le=1000)
    deaths: int = Field(default=0, ge=0, le=1000)
    assists: int = Field(default=0, ge=0, le=1000)
    damage: int = Field(default=0, ge=0)
    objective_score: float = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list, max_length=20)
    note: str | None = Field(default=None, max_length=500)
    played_at: datetime


class PlayerMatchLogOut(PlayerMatchLogIn):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class TimestampNote(BaseModel):
    timestamp: str = Field(max_length=20)
    note: str = Field(min_length=2, max_length=500)


class VODReviewIn(BaseModel):
    player_id: uuid.UUID
    team_id: uuid.UUID
    mode: Mode
    vod_url: str | None = Field(default=None, max_length=500)
    match_date: date
    overall_rating: int = Field(ge=1, le=5)
    strengths: list[str] = Field(default_factory=list, max_length=4)
    weaknesses: list[str] = Field(default_factory=list, max_length=6)
    priority_focus: str = Field(min_length=2, max_length=100)
    timestamp_notes: list[TimestampNote] = Field(default_factory=list, max_length=30)
    note: str | None = Field(default=None, max_length=1000)
    week_start: date


class VODReviewOut(BaseModel):
    id: uuid.UUID
    manager_id: uuid.UUID
    player_id: uuid.UUID
    team_id: uuid.UUID
    mode: Mode
    vod_url: str | None
    match_date: date
    overall_rating: int
    strengths: list[str]
    weaknesses: list[str]
    priority_focus: str
    timestamp_notes: list[dict]
    note: str | None
    ai_findings: list[dict]
    ai_recommendations: list[str]
    analysis_status: AIReviewStatus
    week_start: date
    created_at: datetime

    model_config = {"from_attributes": True}


class WeeklyReviewRunIn(BaseModel):
    week_start: date
    force: bool = False


class WeeklyReviewOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    week_start: date
    status: AIReviewStatus
    performance_score: float | None
    summary_text: str | None
    strengths: list[str]
    weaknesses: list[str]
    focus_points: list[str]
    assigned_drill_ids: list[str]
    generator: str | None
    model_name: str | None
    error_message: str | None
    completed_at: datetime | None

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class TrainingAssignmentOut(BaseModel):
    id: uuid.UUID
    drill_id: uuid.UUID
    sequence: int
    personalized_instruction: str | None
    target_repetitions: int | None
    status: TrainingAssignmentStatus
    completion_notes: str | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CompleteDrillIn(BaseModel):
    completion_notes: str | None = Field(default=None, max_length=1000)


class PerformanceMetricIn(BaseModel):
    user_id: uuid.UUID
    team_id: uuid.UUID | None = None
    mode: Mode
    metric_type: str = Field(min_length=2, max_length=80)
    value: float
    source_type: str = Field(default="coach", max_length=50)
    source_id: uuid.UUID | None = None
    context: dict = Field(default_factory=dict)
