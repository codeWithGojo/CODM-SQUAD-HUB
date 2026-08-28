from __future__ import annotations

import uuid
from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import Mode


class MapGuideIn(BaseModel):
    team_id: uuid.UUID | None = None
    map_name: str = Field(min_length=2, max_length=80)
    mode: Mode
    game_mode: str | None = Field(default=None, max_length=50)
    slot_number: int = Field(ge=1, le=4)
    custom_title: str = Field(min_length=2, max_length=100)
    summary: str | None = Field(default=None, max_length=5000)
    pdf_url: str | None = Field(default=None, max_length=500)
    youtube_url: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list, max_length=20)
    is_curated: bool = False

    @field_validator("pdf_url")
    @classmethod
    def validate_pdf_url(cls, value: str | None):
        if value:
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.netloc or not parsed.path.lower().endswith(".pdf"):
                raise ValueError("pdf_url must be a public HTTPS PDF URL")
        return value

    @field_validator("youtube_url")
    @classmethod
    def validate_youtube_url(cls, value: str | None):
        if value:
            parsed = urlparse(value)
            host = (parsed.hostname or "").lower()
            if parsed.scheme != "https" or host not in {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}:
                raise ValueError("youtube_url must be an HTTPS YouTube URL")
        return value

    @model_validator(mode="after")
    def require_resource(self):
        if not self.pdf_url and not self.youtube_url:
            raise ValueError("Each guide slot needs a PDF URL, YouTube URL, or both")
        return self


class MapGuideOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID | None
    map_name: str
    mode: Mode
    game_mode: str | None
    slot_number: int
    custom_title: str
    summary: str | None
    pdf_url: str | None
    youtube_url: str | None
    tags: list[str]
    is_curated: bool
    is_active: bool
    created_by: uuid.UUID
    approved_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
