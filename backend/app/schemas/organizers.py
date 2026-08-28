from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import TournamentOrganizerStatus


class ApplyOrganizerIn(BaseModel):
    reason_for_applying: str = Field(min_length=20, max_length=1000)
    experience_summary: str | None = Field(default=None, max_length=1000)


class ReviewOrganizerIn(BaseModel):
    status: TournamentOrganizerStatus
    review_note: str | None = Field(default=None, max_length=500)


class OrganizerApplicationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: TournamentOrganizerStatus
    reason_for_applying: str
    experience_summary: str | None
    reviewed_by: uuid.UUID | None
    review_note: str | None
    reviewed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
