from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ChatThreadType, NotificationType


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: NotificationType
    title: str
    body: str
    action_url: str | None
    data: dict
    is_read: bool
    read_at: datetime | None
    created_at: datetime


class DeviceTokenIn(BaseModel):
    token: str | None = Field(default=None, max_length=512)


class ChatThreadIn(BaseModel):
    thread_type: ChatThreadType
    title: str | None = Field(default=None, max_length=150)
    participant_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    team_id: uuid.UUID | None = None
    tournament_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def validate_scope(self):
        if self.thread_type == ChatThreadType.DIRECT and len(set(self.participant_ids)) != 1:
            raise ValueError("A direct thread requires exactly one other participant")
        if self.thread_type == ChatThreadType.TEAM and not self.team_id:
            raise ValueError("team_id is required for a team thread")
        if self.thread_type == ChatThreadType.TOURNAMENT and not self.tournament_id:
            raise ValueError("tournament_id is required for a tournament thread")
        return self


class ChatThreadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    thread_type: ChatThreadType
    title: str | None
    team_id: uuid.UUID | None
    tournament_id: uuid.UUID | None
    created_by: uuid.UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ParticipantIn(BaseModel):
    user_id: uuid.UUID
    is_admin: bool = False


class ChatMessageIn(BaseModel):
    body: str = Field(default="", max_length=4000)
    attachments: list[dict] = Field(default_factory=list, max_length=10)
    reply_to_message_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def non_empty_message(self):
        if not self.body.strip() and not self.attachments:
            raise ValueError("A message must contain text or an attachment")
        return self


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    thread_id: uuid.UUID
    sender_user_id: uuid.UUID
    body: str
    attachments: list[dict]
    reply_to_message_id: uuid.UUID | None
    edited_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime


class ChatMessageEditIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
