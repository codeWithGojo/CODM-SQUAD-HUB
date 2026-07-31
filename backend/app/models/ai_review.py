import uuid
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, ForeignKey, Enum as SAEnum, Integer, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Mode, AIReviewStatus


class VODReview(Base):
    """
    Manager's structured tag-based review of ONE match per player per week.
    This is text/tag data only — NOT automated video analysis (that was
    evaluated and scrapped as not cost-feasible). The manager watches the
    match themselves and fills this short form.
    """
    __tablename__ = "vod_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manager_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)

    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5

    strengths: Mapped[list[str]] = mapped_column(JSON, default=list)   # max 2, from STRENGTH_TAGS
    weaknesses: Mapped[list[str]] = mapped_column(JSON, default=list)  # max 3-4, mode-appropriate tags
    priority_focus: Mapped[str] = mapped_column(String(50), nullable=False)  # one of PRIORITY_FOCUS_OPTIONS
    note: Mapped[str | None] = mapped_column(String(150), nullable=True)

    week_start: Mapped[date] = mapped_column(Date, nullable=False)  # which review-week this counts toward
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DrillPool(Base):
    """
    Curated library of real CoDM training drills, vetted by admins/coaches.
    The AI SELECTS + personalizes from this pool rather than inventing a
    drill from scratch each time — guarantees drills are actually sound,
    and lets us guarantee variety (exclude drills already assigned recently).
    """
    __tablename__ = "drill_pool"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    weakness_category: Mapped[str] = mapped_column(String(50), nullable=False)  # matches a tag from app.core.tags
    mode: Mapped[Mode | None] = mapped_column(SAEnum(Mode), nullable=True)  # null = applies to both
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")  # easy/medium/hard
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AIWeeklyReview(Base):
    """
    The AI-generated output a player receives — delivered async via push
    notification, not generated while they wait in-app.
    Skipped entirely (status=SKIPPED_NO_DATA) if the player logged zero
    matches that week, rather than the AI inventing generic filler.
    """
    __tablename__ = "ai_weekly_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[AIReviewStatus] = mapped_column(SAEnum(AIReviewStatus), default=AIReviewStatus.PENDING)

    summary_text: Mapped[str | None] = mapped_column(String(2000), nullable=True)  # AI coach-style paragraph
    focus_points: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)     # 2-3 training focuses

    # Which DrillPool entries were selected this week, so next week's
    # selection logic can exclude them and stay varied.
    assigned_drill_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    # Raw snapshot of what was sent to the AI — useful for debugging/audit,
    # and for testing different models against the same real input later.
    source_data_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
