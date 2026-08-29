from __future__ import annotations

import json
import re
import uuid
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.models.ai_review import (
    AIWeeklyReview,
    DrillPool,
    PerformanceMetric,
    TrainingAssignment,
    TrainingPlan,
    VODReview,
)
from app.models.competitive import PlayerMatchLog
from app.models.enums import AIReviewStatus, MatchResult, Mode, NotificationType
from app.models.user import User
from app.services.notifications import create_notification


DEFAULT_DRILLS = [
    ("rotation", Mode.MP, "Early Rotation Circuit", "Run three Hardpoint rotations and arrive before the current hill reaches 20 seconds.", 15, "medium", "Reach setup before first enemy contact in 4 of 5 reps."),
    ("trade_spacing", Mode.MP, "Two-Player Trade Lane", "Pair with a teammate and maintain immediate trade distance through five entry routes.", 12, "medium", "Trade within two seconds in 8 of 10 reps."),
    ("positioning", None, "Cover-to-Cover Discipline", "Review and repeat safe routes while eliminating exposed crossings.", 15, "easy", "Complete five routes without an untradeable exposure."),
    ("comms", None, "Three-Word Comms", "Run scenarios using location, damage and intent in every call.", 10, "easy", "Deliver complete calls in 9 of 10 scenarios."),
    ("aim", None, "Tracking Ladder", "Use training range targets at three distances, increasing speed after each clean set.", 15, "medium", "Maintain 70% tracking accuracy across the final set."),
    ("objective", Mode.MP, "Objective Timing Block", "Rehearse entry, trophy placement and anchor hand-off around two objective setups.", 20, "hard", "Win four complete setup simulations."),
    ("decision_making", Mode.BR, "Final-Zone Decision Tree", "Review five late-zone states and call rotate, hold or fight with one reason.", 15, "medium", "Choose the coach-approved option in 4 of 5 states."),
    ("survival", Mode.BR, "Reset and Reposition", "Practice disengaging, plating and re-entering from a new angle.", 12, "medium", "Complete six resets without re-peeking the same angle."),
]


def ensure_default_drills(db: Session) -> None:
    if db.query(DrillPool.id).first():
        return
    for category, mode, title, description, duration, difficulty, metric in DEFAULT_DRILLS:
        db.add(
            DrillPool(
                weakness_category=category,
                mode=mode,
                title=title,
                description=description,
                duration_minutes=duration,
                difficulty=difficulty,
                success_metric=metric,
            )
        )
    db.flush()


def generate_weekly_review(
    db: Session,
    *,
    user: User,
    week_start: date,
    force: bool = False,
) -> AIWeeklyReview:
    existing = db.query(AIWeeklyReview).filter_by(user_id=user.id, week_start=week_start).first()
    if existing and not force:
        return existing
    review = existing or AIWeeklyReview(user_id=user.id, week_start=week_start)
    if not existing:
        db.add(review)
    review.status = AIReviewStatus.PROCESSING
    review.error_message = None
    db.flush()

    snapshot = aggregate_week(db, user_id=user.id, week_start=week_start)
    review.source_data_snapshot = snapshot
    if snapshot["matches"] == 0:
        review.status = AIReviewStatus.SKIPPED_NO_DATA
        review.completed_at = utcnow()
        review.summary_text = "No weekly review was generated because no matches were logged this week."
        return review

    try:
        output, generator, model_name = _generate_coach_output(snapshot, user)
    except Exception as exc:
        if not settings.ai_allow_rules_fallback:
            review.status = AIReviewStatus.FAILED
            review.error_message = str(exc)[:1000]
            review.completed_at = utcnow()
            return review
        output = rules_based_output(snapshot, user)
        generator, model_name = "rules", None

    review.performance_score = output["performance_score"]
    review.summary_text = output["summary"]
    review.strengths = output["strengths"][:4]
    review.weaknesses = output["weaknesses"][:4]
    review.focus_points = output["focus_points"][:3]
    review.generator = generator
    review.model_name = model_name
    review.status = AIReviewStatus.READY
    review.completed_at = utcnow()

    plan = _upsert_training_plan(db, review, output)
    review.assigned_drill_ids = [str(row.drill_id) for row in db.query(TrainingAssignment).filter_by(training_plan_id=plan.id).all()]
    create_notification(
        db,
        user_id=user.id,
        notification_type=NotificationType.AI_REVIEW,
        title="Your weekly AI review is ready",
        body=output["summary"][:240],
        action_url="/performance/weekly-review",
        data={"review_id": str(review.id), "week_start": str(week_start)},
    )
    return review


def aggregate_week(db: Session, *, user_id: uuid.UUID, week_start: date) -> dict:
    start = datetime.combine(week_start, time.min, tzinfo=UTC)
    end = start + timedelta(days=7)
    matches = (
        db.query(PlayerMatchLog)
        .filter(PlayerMatchLog.user_id == user_id, PlayerMatchLog.played_at >= start, PlayerMatchLog.played_at < end)
        .order_by(PlayerMatchLog.played_at.asc())
        .all()
    )
    vod = db.query(VODReview).filter(VODReview.player_id == user_id, VODReview.week_start == week_start).all()
    metrics = (
        db.query(PerformanceMetric)
        .filter(PerformanceMetric.user_id == user_id, PerformanceMetric.captured_at >= start, PerformanceMetric.captured_at < end)
        .all()
    )
    kills = sum(row.kills for row in matches)
    deaths = sum(row.deaths for row in matches)
    assists = sum(row.assists for row in matches)
    wins = sum(1 for row in matches if row.result == MatchResult.WIN)
    tags = Counter(tag for row in matches for tag in row.tags)
    strengths = Counter(tag for row in vod for tag in row.strengths)
    weaknesses = Counter(tag for row in vod for tag in row.weaknesses)
    return {
        "week_start": str(week_start),
        "matches": len(matches),
        "wins": wins,
        "win_rate": round(wins / len(matches), 3) if matches else 0,
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kd": round(kills / max(1, deaths), 2),
        "average_objective_score": round(sum(float(row.objective_score) for row in matches) / len(matches), 2) if matches else 0,
        "repeat_tags": dict(tags.most_common(8)),
        "manager_strengths": dict(strengths.most_common(6)),
        "manager_weaknesses": dict(weaknesses.most_common(6)),
        "vod_reviews": len(vod),
        "metric_samples": [{"type": row.metric_type, "value": float(row.value)} for row in metrics[:50]],
    }


def rules_based_output(snapshot: dict, user: User) -> dict:
    score = 50 + snapshot["win_rate"] * 25 + min(15, snapshot["kd"] * 6) + min(10, snapshot["average_objective_score"] / 10)
    score = round(max(0, min(100, score)), 1)
    weakness_candidates = list(snapshot["manager_weaknesses"]) + list(snapshot["repeat_tags"])
    weaknesses = _normalized_focuses(weakness_candidates) or ["decision_making"]
    strengths = list(snapshot["manager_strengths"]) or (["objective impact"] if snapshot["average_objective_score"] else ["consistent match logging"])
    focuses = weaknesses[:3]
    summary = (
        f"You logged {snapshot['matches']} matches with a {snapshot['win_rate'] * 100:.0f}% win rate and "
        f"{snapshot['kd']:.2f} K/D. Your next block should focus on {', '.join(value.replace('_', ' ') for value in focuses)}."
    )
    return {
        "performance_score": score,
        "summary": summary,
        "strengths": strengths[:4],
        "weaknesses": weaknesses[:4],
        "focus_points": focuses,
    }


def _generate_coach_output(snapshot: dict, user: User) -> tuple[dict, str, str | None]:
    if not settings.gemini_api_key:
        if settings.ai_allow_rules_fallback:
            return rules_based_output(snapshot, user), "rules", None
        raise RuntimeError("GEMINI_API_KEY is not configured")
    prompt = {
        "role": "You are an advisory Call of Duty: Mobile performance coach. Never alter rankings or issue discipline.",
        "player": {"mode": user.preferred_mode.value if user.preferred_mode else None},
        "weekly_data": snapshot,
        "required_json": {
            "performance_score": "number 0-100",
            "summary": "plain-language paragraph under 120 words",
            "strengths": "array of 2-4 short strings",
            "weaknesses": "array of 2-4 short strings",
            "focus_points": "array of exactly 2-3 actionable categories",
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    response = httpx.post(
        url,
        params={"key": settings.gemini_api_key},
        json={
            "contents": [{"role": "user", "parts": [{"text": json.dumps(prompt)}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.25},
        },
        timeout=25.0,
    )
    response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    data = json.loads(text)
    required = {"performance_score", "summary", "strengths", "weaknesses", "focus_points"}
    if not required.issubset(data):
        raise ValueError("Gemini response omitted required coaching fields")
    data["performance_score"] = max(0, min(100, float(data["performance_score"])))
    return data, "gemini", settings.gemini_model


def analyze_vod_review(review: VODReview) -> tuple[list[dict], list[str], str, str | None]:
    payload = {
        "mode": review.mode.value,
        "overall_rating": review.overall_rating,
        "strengths": review.strengths,
        "weaknesses": review.weaknesses,
        "priority_focus": review.priority_focus,
        "timestamp_notes": review.timestamp_notes,
        "manager_note": review.note,
    }
    if settings.gemini_api_key:
        prompt = {
            "instruction": "Turn structured CODM VOD notes into timestamped findings and practical recommendations. Do not claim to have watched the video.",
            "data": payload,
            "required_json": {"findings": [{"timestamp": "string", "finding": "string"}], "recommendations": ["string"]},
        }
        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
            params={"key": settings.gemini_api_key},
            json={"contents": [{"parts": [{"text": json.dumps(prompt)}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}},
            timeout=25.0,
        )
        response.raise_for_status()
        data = json.loads(response.json()["candidates"][0]["content"]["parts"][0]["text"])
        return data.get("findings", [])[:20], data.get("recommendations", [])[:8], "gemini", settings.gemini_model
    findings = [
        {"timestamp": str(item.get("timestamp", "review")), "finding": str(item.get("note", item.get("finding", "Decision point flagged by coach")))}
        for item in review.timestamp_notes[:20]
    ]
    recommendations = [f"Run a focused {value.replace('_', ' ')} drill" for value in _normalized_focuses(review.weaknesses + [review.priority_focus])[:4]]
    return findings, recommendations, "rules", None


def _upsert_training_plan(db: Session, review: AIWeeklyReview, output: dict) -> TrainingPlan:
    ensure_default_drills(db)
    old = db.query(TrainingPlan).filter_by(user_id=review.user_id, week_start=review.week_start).first()
    if old:
        db.query(TrainingAssignment).filter_by(training_plan_id=old.id).delete()
        plan = old
        plan.weekly_review_id = review.id
        plan.goals = output["focus_points"][:3]
        plan.generated_by = review.generator or "rules"
    else:
        plan = TrainingPlan(
            user_id=review.user_id,
            weekly_review_id=review.id,
            week_start=review.week_start,
            title=f"Weekly Development Plan — {review.week_start}",
            goals=output["focus_points"][:3],
            generated_by=review.generator or "rules",
        )
        db.add(plan)
        db.flush()

    categories = _normalized_focuses(output["focus_points"] + output["weaknesses"])
    assigned: list[DrillPool] = []
    for category in categories:
        candidate = db.query(DrillPool).filter(DrillPool.weakness_category == category, DrillPool.is_active.is_(True)).first()
        if candidate and candidate not in assigned:
            assigned.append(candidate)
    if len(assigned) < 3:
        extras = db.query(DrillPool).filter(DrillPool.is_active.is_(True)).limit(6).all()
        assigned.extend(row for row in extras if row not in assigned)
    assigned = assigned[:4]
    plan.total_minutes = sum(row.duration_minutes for row in assigned)
    for sequence, drill in enumerate(assigned, 1):
        db.add(
            TrainingAssignment(
                training_plan_id=plan.id,
                drill_id=drill.id,
                sequence=sequence,
                personalized_instruction=f"Prioritised because this week's review flagged {drill.weakness_category.replace('_', ' ')}.",
            )
        )
    db.flush()
    return plan


def _normalized_focuses(values: list[str]) -> list[str]:
    output: list[str] = []
    for raw in values:
        value = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
        if "rotat" in value:
            value = "rotation"
        elif "trade" in value or "spacing" in value:
            value = "trade_spacing"
        elif "position" in value or "overextend" in value:
            value = "positioning"
        elif "comm" in value or "callout" in value:
            value = "comms"
        elif "aim" in value or "track" in value or "gunfight" in value:
            value = "aim"
        elif "objective" in value or "hill" in value:
            value = "objective"
        elif "surviv" in value or "reset" in value:
            value = "survival"
        else:
            value = "decision_making"
        if value not in output:
            output.append(value)
    return output
