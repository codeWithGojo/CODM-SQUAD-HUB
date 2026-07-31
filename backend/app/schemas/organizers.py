import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import TournamentOrganizerStatus


class TournamentOrganizerApplication(Base):
    """
    'Anyone can apply' (locked decision) — but applying isn't the same as
    being approved. Only APPROVED applicants can resolve disputes or
    configure Transfer Windows. Kept as its own table (not a flag on
    User) so the approval history/reasoning is preserved.
    """
    __tablename__ = "tournament_organizer_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    status: Mapped[TournamentOrganizerStatus] = mapped_column(
        SAEnum(TournamentOrganizerStatus), default=TournamentOrganizerStatus.PENDING
    )
    reason_for_applying: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)