from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.models.enums import BlacklistStatus, BlacklistSubjectType, DisputeStatus, SanctionType


class TournamentDispute(Base):
    __tablename__ = "tournament_disputes"
    __table_args__ = (Index("dispute_status_created_idx", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tournament_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tournaments.id"), nullable=False)
    match_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tournament_matches.id"), nullable=True)
    filed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    filing_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    against_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(SAEnum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False)
    ruling: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class BlacklistEntry(Base):
    """CRA competitive-integrity blacklist with evidence, scope, and appeal state."""

    __tablename__ = "blacklist_entries"
    __table_args__ = (
        Index("blacklist_subject_active_idx", "subject_type", "subject_id", "status"),
        Index("blacklist_expiry_idx", "status", "ends_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_type: Mapped[BlacklistSubjectType] = mapped_column(SAEnum(BlacklistSubjectType), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    subject_name_snapshot: Mapped[str] = mapped_column(String(150), nullable=False)
    sanction_type: Mapped[SanctionType] = mapped_column(SAEnum(SanctionType), nullable=False)
    status: Mapped[BlacklistStatus] = mapped_column(SAEnum(BlacklistStatus), default=BlacklistStatus.ACTIVE, nullable=False)
    scope: Mapped[str] = mapped_column(String(50), default="platform", nullable=False)
    public_reason: Mapped[str] = mapped_column(String(500), nullable=False)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    related_dispute_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tournament_disputes.id"), nullable=True)
    issued_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class BlacklistAppeal(Base):
    __tablename__ = "blacklist_appeals"
    __table_args__ = (Index("blacklist_appeal_status_idx", "status", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    blacklist_entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("blacklist_entries.id"), nullable=False)
    filed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(SAEnum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False)
    decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
