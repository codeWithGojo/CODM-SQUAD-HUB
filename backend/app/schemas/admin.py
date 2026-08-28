from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import NotificationType, VerificationStatus


class UserBanIn(BaseModel):
    banned: bool
    reason: str | None = Field(default=None, max_length=255)
    banned_until: datetime | None = None


class VerificationIn(BaseModel):
    status: VerificationStatus
    note: str | None = Field(default=None, max_length=500)


class AchievementVerificationIn(BaseModel):
    verified: bool
    note: str | None = Field(default=None, max_length=500)


class ReportIn(BaseModel):
    reported_user_id: uuid.UUID
    category: str = Field(default="misconduct", min_length=3, max_length=50)
    reason: str = Field(min_length=10, max_length=5000)
    evidence_urls: list[str] = Field(default_factory=list, max_length=10)


class ReportReviewIn(BaseModel):
    review_note: str = Field(min_length=3, max_length=1000)


class BroadcastNotificationIn(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    body: str = Field(min_length=3, max_length=1000)
    notification_type: NotificationType = NotificationType.SYSTEM
    action_url: str | None = Field(default=None, max_length=500)
    user_ids: list[uuid.UUID] = Field(default_factory=list, max_length=1000)


class RumourPublishIn(BaseModel):
    is_public: bool
