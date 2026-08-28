from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.models.enums import TournamentOrganizerStatus


class TournamentOrganizerApplication(Base):
    __tablename__ = "tournament_organizer_applications"
    __table_args__ = (Index("organizer_application_status_idx", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    reason_for_applying: Mapped[str] = mapped_column(String(1000), nullable=False)
    experience_summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[TournamentOrganizerStatus] = mapped_column(
        SAEnum(TournamentOrganizerStatus), default=TournamentOrganizerStatus.PENDING, nullable=False
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
