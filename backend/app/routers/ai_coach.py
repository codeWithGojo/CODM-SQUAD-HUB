from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.deps import get_current_user, require_platform_admin
from app.core.time import utcnow
from app.models.ai_review import (
    AIWeeklyReview,
    PerformanceMetric,
    TrainingAssignment,
    TrainingPlan,
    VODReview,
)
from app.models.competitive import PlayerMatchLog
from app.models.enums import AIReviewStatus, TrainingAssignmentStatus
from app.models.team import TeamMember
from app.models.user import User
from app.schemas.ai_coach import (
    CompleteDrillIn,
    PerformanceMetricIn,
    PlayerMatchLogIn,
    PlayerMatchLogOut,
    VODReviewIn,
    VODReviewOut,
    WeeklyReviewOut,
    WeeklyReviewRunIn,
)
from app.services.ai_coach import aggregate_week, analyze_vod_review, generate_weekly_review
from app.services.permissions import require_team_manager
from app.services.realtime import realtime

router = APIRouter(tags=["performance-and-ai"])


@router.post("/performance/matches", response_model=PlayerMatchLogOut, status_code=status.HTTP_201_CREATED)
def log_match(
    payload: PlayerMatchLogIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.team_id and not db.query(TeamMember.id).filter_by(
        team_id=payload.team_id,
        user_id=current_user.id,
        is_active=True,
    ).first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only log team-scoped matches for your active roster.")
    row = PlayerMatchLog(user_id=current_user.id, **payload.model_dump())
    db.add(row)
    db.flush()
    if row.deaths:
        db.add(PerformanceMetric(user_id=current_user.id, team_id=row.team_id, mode=row.mode, metric_type="kd", value=row.kills / row.deaths, source_type="match_log", source_id=row.id))
    db.add(PerformanceMetric(user_id=current_user.id, team_id=row.team_id, mode=row.mode, metric_type="objective_score", value=row.objective_score, source_type="match_log", source_id=row.id))
    db.commit()
    db.refresh(row)
    return row


@router.get("/performance/me/analytics")
def my_analytics(
    days: int = Query(default=30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = utcnow() - timedelta(days=days)
    rows = db.query(PlayerMatchLog).filter(PlayerMatchLog.user_id == current_user.id, PlayerMatchLog.played_at >= start).all()
    kills = sum(row.kills for row in rows)
    deaths = sum(row.deaths for row in rows)
    wins = sum(1 for row in rows if row.result and row.result.value == "win")
    return {
        "days": days,
        "matches": len(rows),
        "wins": wins,
        "win_rate": round(wins / len(rows), 3) if rows else 0,
        "kd": round(kills / max(1, deaths), 2),
        "average_damage": round(sum(row.damage for row in rows) / len(rows), 1) if rows else 0,
        "average_objective_score": round(sum(float(row.objective_score) for row in rows) / len(rows), 2) if rows else 0,
    }


@router.post("/performance/metrics", status_code=status.HTTP_201_CREATED)
def add_performance_metric(
    payload: PerformanceMetricIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.team_id:
        require_team_manager(db, payload.team_id, current_user)
        if not db.query(TeamMember.id).filter_by(
            team_id=payload.team_id,
            user_id=payload.user_id,
            is_active=True,
        ).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Metric player is not active on this team.")
    elif payload.user_id != current_user.id and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot add metrics for another player.")
    row = PerformanceMetric(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/ai/vod-reviews", response_model=VODReviewOut, status_code=status.HTTP_201_CREATED)
def create_vod_review(
    payload: VODReviewIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, payload.team_id, current_user)
    if not db.query(TeamMember.id).filter_by(
        team_id=payload.team_id,
        user_id=payload.player_id,
        is_active=True,
    ).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VOD review player is not active on this team.")
    row = VODReview(
        manager_id=current_user.id,
        **payload.model_dump(exclude={"timestamp_notes"}),
        timestamp_notes=[item.model_dump() for item in payload.timestamp_notes],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/ai/vod-reviews/{review_id}/analyze", response_model=VODReviewOut)
def analyze_vod(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(VODReview, review_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VOD review not found.")
    require_team_manager(db, row.team_id, current_user)
    row.analysis_status = AIReviewStatus.PROCESSING
    try:
        findings, recommendations, _generator, _model = analyze_vod_review(row)
        row.ai_findings = findings
        row.ai_recommendations = recommendations
        row.analysis_status = AIReviewStatus.READY
    except Exception as exc:
        row.analysis_status = AIReviewStatus.FAILED
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI review failed: {str(exc)[:300]}") from exc
    db.commit()
    db.refresh(row)
    return row


@router.get("/ai/vod-reviews/me", response_model=list[VODReviewOut])
def my_vod_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(VODReview).filter(VODReview.player_id == current_user.id).order_by(VODReview.created_at.desc()).limit(100).all()


@router.post("/ai/weekly-reviews/run", response_model=WeeklyReviewOut)
def run_my_weekly_review(
    payload: WeeklyReviewRunIn,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = generate_weekly_review(db, user=current_user, week_start=payload.week_start, force=payload.force)
    db.commit()
    db.refresh(row)
    background_tasks.add_task(
        realtime.send_user,
        current_user.id,
        {"type": "ai_review.ready", "review_id": str(row.id), "status": row.status.value},
    )
    return row


@router.get("/ai/weekly-reviews/me", response_model=list[WeeklyReviewOut])
def my_weekly_reviews(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(AIWeeklyReview).filter_by(user_id=current_user.id).order_by(AIWeeklyReview.week_start.desc()).limit(limit).all()


@router.get("/ai/training-plans/me")
def my_training_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    plans = db.query(TrainingPlan).filter_by(user_id=current_user.id).order_by(TrainingPlan.week_start.desc()).limit(20).all()
    return [
        {
            "plan": plan,
            "assignments": db.query(TrainingAssignment).filter_by(training_plan_id=plan.id).order_by(TrainingAssignment.sequence).all(),
        }
        for plan in plans
    ]


@router.patch("/ai/training-assignments/{assignment_id}/complete")
def complete_drill(
    assignment_id: uuid.UUID,
    payload: CompleteDrillIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assignment = db.get(TrainingAssignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training assignment not found.")
    plan = db.get(TrainingPlan, assignment.training_plan_id)
    if not plan or plan.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This drill is not assigned to you.")
    assignment.status = TrainingAssignmentStatus.COMPLETED
    assignment.completion_notes = payload.completion_notes
    assignment.completed_at = utcnow()
    db.commit()
    db.refresh(assignment)
    return assignment


def _run_weekly_batch(week_start: date) -> None:
    db = SessionLocal()
    try:
        start = datetime.combine(week_start, time.min, tzinfo=UTC)
        end = start + timedelta(days=7)
        user_ids = [row[0] for row in db.query(PlayerMatchLog.user_id).filter(PlayerMatchLog.played_at >= start, PlayerMatchLog.played_at < end).distinct().all()]
        for user_id in user_ids:
            user = db.get(User, user_id)
            if user:
                generate_weekly_review(db, user=user, week_start=week_start)
        db.commit()
    finally:
        db.close()


@router.post("/ai/jobs/weekly", status_code=status.HTTP_202_ACCEPTED)
def queue_weekly_batch(
    payload: WeeklyReviewRunIn,
    background_tasks: BackgroundTasks,
    _admin: User = Depends(require_platform_admin),
):
    background_tasks.add_task(_run_weekly_batch, payload.week_start)
    return {"status": "queued", "week_start": payload.week_start}
