from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import Mode, RankingEntityType, RankingScope


class SeasonIn(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    code: str = Field(min_length=2, max_length=40, pattern=r"^[A-Z0-9_-]+$")
    starts_on: date
    ends_on: date
    is_active: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.ends_on <= self.starts_on:
            raise ValueError("ends_on must be after starts_on")
        return self


class SeasonOut(SeasonIn):
    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class RecalculateRankingsIn(BaseModel):
    season_id: uuid.UUID
    mode: Mode


class RankingSnapshotOut(BaseModel):
    id: uuid.UUID
    calculation_id: uuid.UUID
    season_id: uuid.UUID
    mode: Mode
    entity_type: RankingEntityType
    entity_id: uuid.UUID
    entity_name: str
    scope: RankingScope
    scope_code: str
    rating: float
    points: float
    rank: int
    previous_rank: int | None
    movement: int
    matches_played: int
    wins: int
    losses: int
    explanation: dict
    generated_at: datetime

    model_config = {"from_attributes": True}
