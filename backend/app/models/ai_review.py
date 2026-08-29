from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow
from app.models.enums import AIReviewStatus, Mode, TrainingAssignmentStatus


class VODReview(Base):
    """Structured manager tags and timestamps; the AI reasons over this data, not raw video bytes."""

    __tablename__ = "vod_reviews"
    __table_args__ = (Index("vod_player_week_idx", "player_id", "week_start"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    manager_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    vod_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    priority_focus: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp_notes: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    ai_findings: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    ai_recommendations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    analysis_status: Mapped[AIReviewStatus] = mapped_column(
        SAEnum(AIReviewStatus), default=AIReviewStatus.PENDING, nullable=False
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class DrillPool(Base):
    __tablename__ = "drill_pool"
    __table_args__ = (Index("drill_pool_lookup_idx", "weakness_category", "mode", "is_active"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    weakness_category: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[Mode | None] = mapped_column(SAEnum(Mode), nullable=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    equipment: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    success_metric: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    __table_args__ = (Index("performance_user_metric_time_idx", "user_id", "metric_type", "captured_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    mode: Mapped[Mode] = mapped_column(SAEnum(Mode), nullable=False)
    metric_type: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="match_log", nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TrainingPlan(Base):
    __tablename__ = "training_plans"
    __table_args__ = (UniqueConstraint("user_id", "week_start", name="uq_user_week_training_plan"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), nullable=True)
    weekly_review_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("ai_weekly_reviews.id"), nullable=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    goals: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    total_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generated_by: Mapped[str] = mapped_column(String(30), default="rules", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class TrainingAssignment(Base):
    __tablename__ = "training_assignments"
    __table_args__ = (Index("training_assignment_plan_status_idx", "training_plan_id", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_plans.id"), nullable=False)
    drill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("drill_pool.id"), nullable=False)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    personalized_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_repetitions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[TrainingAssignmentStatus] = mapped_column(
        SAEnum(TrainingAssignmentStatus), default=TrainingAssignmentStatus.ASSIGNED, nullable=False
    )
    completion_notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AIWeeklyReview(Base):
    __tablename__ = "ai_weekly_reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_user_week_ai_review"),
        Index("ai_review_status_week_idx", "status", "week_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AIReviewStatus] = mapped_column(
        SAEnum(AIReviewStatus), default=AIReviewStatus.PENDING, nullable=False
    )
    performance_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    focus_points: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    assigned_drill_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source_data_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    generator: Mapped[str | None] = mapped_column(String(40), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
