from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ChallengeStatus, Mode, ScrimStatus


class ChallengeIn(BaseModel):
    challenger_team_id: uuid.UUID
    challenged_team_id: uuid.UUID
    mode: Mode
    format: str = Field(default="BO5", min_length=2, max_length=50)
    scheduled_at: datetime | None = None
    expires_in_hours: int = Field(default=48, ge=1, le=168)

    @model_validator(mode="after")
    def different_teams(self):
        if self.challenger_team_id == self.challenged_team_id:
            raise ValueError("A team cannot challenge itself")
        return self


class ChallengeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    challenger_team_id: uuid.UUID
    challenged_team_id: uuid.UUID
    created_by: uuid.UUID
    mode: Mode
    format: str
    status: ChallengeStatus
    scheduled_at: datetime | None
    expires_at: datetime | None
    score_challenger: int | None
    score_challenged: int | None
    score_details: dict
    proof_screenshot_url: str | None
    result_reported_by: uuid.UUID | None
    result_reported_team_id: uuid.UUID | None
    result_confirmed_by: uuid.UUID | None
    verified_at: datetime | None
    created_at: datetime


class ChallengeResponseIn(BaseModel):
    accept: bool


class ChallengeResultIn(BaseModel):
    score_challenger: int = Field(ge=0, le=1000)
    score_challenged: int = Field(ge=0, le=1000)
    score_details: dict = Field(default_factory=dict)
    proof_screenshot_url: str = Field(min_length=5, max_length=500)


class ChallengeConfirmIn(BaseModel):
    confirm: bool
    reason: str | None = Field(default=None, max_length=500)


class ScrimIn(BaseModel):
    team_id: uuid.UUID
    opponent_team_id: uuid.UUID | None = None
    opponent_name: str | None = Field(default=None, max_length=100)
    mode: Mode
    format: str = Field(default="BO5", min_length=2, max_length=50)
    maps: list[str] = Field(default_factory=list, max_length=20)
    requirements: dict = Field(default_factory=dict)
    scheduled_at: datetime
    is_open: bool = False

    @model_validator(mode="after")
    def opponent_or_open(self):
        if not self.is_open and not (self.opponent_team_id or self.opponent_name):
            raise ValueError("Choose an opponent or publish the scrim as open")
        if self.opponent_team_id == self.team_id:
            raise ValueError("A team cannot scrim itself")
        return self


class ScrimStatusIn(BaseModel):
    status: ScrimStatus


class ScrimClaimIn(BaseModel):
    opponent_team_id: uuid.UUID
