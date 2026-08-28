from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.models.enums import ChatThreadType, NotificationType


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("notification_user_read_idx", "user_id", "is_read", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType), default=NotificationType.SYSTEM, nullable=False
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    body: Mapped[str] = mapped_column(String(1000), nullable=False)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    push_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    push_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ChatThread(Base):
    __tablename__ = "chat_threads"
    __table_args__ = (Index("chat_thread_updated_idx", "updated_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    direct_key: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    thread_type: Mapped[ChatThreadType] = mapped_column(
        SAEnum(ChatThreadType), default=ChatThreadType.DIRECT, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    tournament_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tournaments.id"), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class ChatParticipant(Base):
    __tablename__ = "chat_participants"
    __table_args__ = (
        UniqueConstraint("thread_id", "user_id", name="uq_chat_thread_participant"),
        Index("chat_participant_user_idx", "user_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_threads.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = (Index("chat_message_thread_time_idx", "thread_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_threads.id"), nullable=False)
    sender_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    reply_to_message_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chat_messages.id"), nullable=True)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
