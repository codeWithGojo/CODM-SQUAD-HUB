from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_platform_admin
from app.core.time import as_utc, utcnow
from app.models.competitive import Challenge, OfficialTeamResult, Scrim
from app.models.enums import ChallengeStatus, MatchResult, Mode, NotificationType, ScrimStatus
from app.models.team import Team
from app.models.user import User
from app.schemas.competitive import (
    ChallengeConfirmIn,
    ChallengeIn,
    ChallengeOut,
    ChallengeResponseIn,
    ChallengeResultIn,
    ScrimClaimIn,
    ScrimIn,
    ScrimStatusIn,
)
from app.services.notifications import create_notification
from app.services.permissions import require_team_manager
from app.services.realtime import realtime

router = APIRouter(tags=["challenges-and-scrims"])


def _expire_challenges(db: Session) -> int:
    rows = (
        db.query(Challenge)
        .filter(
            Challenge.status == ChallengeStatus.PENDING,
            Challenge.expires_at.is_not(None),
            Challenge.expires_at <= utcnow(),
        )
        .all()
    )
    for row in rows:
        row.status = ChallengeStatus.CANCELLED
    return len(rows)


def _challenge_or_404(db: Session, challenge_id: uuid.UUID) -> Challenge:
    row = db.get(Challenge, challenge_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")
    return row


def _notify_manager(db: Session, team_id: uuid.UUID, title: str, body: str, action_url: str) -> None:
    team = db.get(Team, team_id)
    if team and team.manager_id:
        create_notification(
            db,
            user_id=team.manager_id,
            notification_type=NotificationType.MATCH,
            title=title,
            body=body,
            action_url=action_url,
        )


@router.post("/challenges", response_model=ChallengeOut, status_code=status.HTTP_201_CREATED)
def create_challenge(
    payload: ChallengeIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenger = require_team_manager(db, payload.challenger_team_id, current_user)
    challenged = db.get(Team, payload.challenged_team_id)
    if not challenged:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenged team not found.")
    if db.query(Challenge.id).filter(
        Challenge.challenger_team_id == challenger.id,
        Challenge.challenged_team_id == challenged.id,
        Challenge.status.in_([ChallengeStatus.PENDING, ChallengeStatus.ACCEPTED]),
    ).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An open challenge already exists between these teams.")
    row = Challenge(
        challenger_team_id=challenger.id,
        challenged_team_id=challenged.id,
        created_by=current_user.id,
        mode=payload.mode,
        format=payload.format,
        scheduled_at=payload.scheduled_at,
        expires_at=utcnow() + timedelta(hours=payload.expires_in_hours),
    )
    db.add(row)
    db.flush()
    _notify_manager(db, challenged.id, "New team challenge", f"{challenger.name} challenged your team.", f"/challenges/{row.id}")
    db.commit()
    db.refresh(row)
    return row


@router.get("/challenges", response_model=list[ChallengeOut])
def list_challenges(
    team_id: uuid.UUID | None = None,
    challenge_status: ChallengeStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    changed = _expire_challenges(db)
    query = db.query(Challenge)
    if team_id:
        query = query.filter(or_(Challenge.challenger_team_id == team_id, Challenge.challenged_team_id == team_id))
    if challenge_status:
        query = query.filter(Challenge.status == challenge_status)
    rows = query.order_by(Challenge.created_at.desc()).limit(limit).all()
    if changed:
        db.commit()
    return rows


@router.post("/challenges/{challenge_id}/respond", response_model=ChallengeOut)
def respond_to_challenge(
    challenge_id: uuid.UUID,
    payload: ChallengeResponseIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _challenge_or_404(db, challenge_id)
    require_team_manager(db, row.challenged_team_id, current_user)
    if row.status != ChallengeStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Challenge is no longer pending.")
    if row.expires_at and as_utc(row.expires_at) <= utcnow():
        row.status = ChallengeStatus.CANCELLED
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Challenge has expired.")
    row.status = ChallengeStatus.ACCEPTED if payload.accept else ChallengeStatus.DECLINED
    _notify_manager(
        db,
        row.challenger_team_id,
        "Challenge accepted" if payload.accept else "Challenge declined",
        "The opposing manager responded to your challenge.",
        f"/challenges/{row.id}",
    )
    db.commit()
    db.refresh(row)
    return row


@router.post("/challenges/{challenge_id}/result", response_model=ChallengeOut)
def report_challenge_result(
    challenge_id: uuid.UUID,
    payload: ChallengeResultIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _challenge_or_404(db, challenge_id)
    if row.status != ChallengeStatus.ACCEPTED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only an accepted challenge can receive a result.")
    if row.result_reported_by:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A result is already awaiting confirmation.")
    managed_team = None
    for team_id in (row.challenger_team_id, row.challenged_team_id):
        try:
            require_team_manager(db, team_id, current_user)
            managed_team = team_id
            break
        except HTTPException:
            pass
    if not managed_team:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Participating team manager access required.")
    row.score_challenger = payload.score_challenger
    row.score_challenged = payload.score_challenged
    row.score_details = payload.score_details
    row.proof_screenshot_url = payload.proof_screenshot_url
    row.result_reported_by = current_user.id
    row.result_reported_team_id = managed_team
    opponent_id = row.challenged_team_id if managed_team == row.challenger_team_id else row.challenger_team_id
    _notify_manager(db, opponent_id, "Challenge result needs confirmation", "Review the score and proof submitted by the opposing manager.", f"/challenges/{row.id}")
    db.commit()
    db.refresh(row)
    return row


def _finalize_result(db: Session, row: Challenge, verifier_id: uuid.UUID) -> None:
    if row.score_challenger is None or row.score_challenged is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No result has been reported.")
    db.query(OfficialTeamResult).filter_by(challenge_id=row.id).delete()
    draw = row.score_challenger == row.score_challenged
    challenger_result = MatchResult.DRAW if draw else (MatchResult.WIN if row.score_challenger > row.score_challenged else MatchResult.LOSS)
    challenged_result = MatchResult.DRAW if draw else (MatchResult.WIN if row.score_challenged > row.score_challenger else MatchResult.LOSS)
    played_at = row.scheduled_at or utcnow()
    for team_id, opponent_id, result, score_for, score_against in (
        (row.challenger_team_id, row.challenged_team_id, challenger_result, row.score_challenger, row.score_challenged),
        (row.challenged_team_id, row.challenger_team_id, challenged_result, row.score_challenged, row.score_challenger),
    ):
        db.add(
            OfficialTeamResult(
                team_id=team_id,
                opponent_team_id=opponent_id,
                challenge_id=row.id,
                mode=row.mode,
                result=result,
                score_for=score_for,
                score_against=score_against,
                score_details=row.score_details,
                submitted_by=row.result_reported_by or verifier_id,
                proof_screenshot_url=row.proof_screenshot_url,
                is_verified=True,
                verified_by=verifier_id,
                verified_at=utcnow(),
                played_at=played_at,
            )
        )
    row.status = ChallengeStatus.COMPLETED
    row.result_confirmed_by = verifier_id
    row.verified_at = utcnow()


@router.post("/challenges/{challenge_id}/confirm", response_model=ChallengeOut)
def confirm_challenge_result(
    challenge_id: uuid.UUID,
    payload: ChallengeConfirmIn,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _challenge_or_404(db, challenge_id)
    if not row.result_reported_by:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No result has been reported.")
    confirming_team = (
        row.challenged_team_id
        if row.result_reported_team_id == row.challenger_team_id
        else row.challenger_team_id
    )
    require_team_manager(db, confirming_team, current_user)
    if payload.confirm:
        _finalize_result(db, row, current_user.id)
    else:
        row.status = ChallengeStatus.DISPUTED
    db.commit()
    db.refresh(row)
    background_tasks.add_task(
        realtime.publish_channel,
        f"challenge:{row.id}",
        {"type": "challenge.result_confirmed" if payload.confirm else "challenge.disputed", "challenge_id": str(row.id)},
    )
    return row


@router.post("/challenges/{challenge_id}/resolve", response_model=ChallengeOut)
def resolve_challenge_dispute(
    challenge_id: uuid.UUID,
    payload: ChallengeResultIn,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    row = _challenge_or_404(db, challenge_id)
    if row.status != ChallengeStatus.DISPUTED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Challenge is not disputed.")
    row.score_challenger = payload.score_challenger
    row.score_challenged = payload.score_challenged
    row.score_details = payload.score_details
    row.proof_screenshot_url = payload.proof_screenshot_url
    _finalize_result(db, row, admin.id)
    db.commit()
    db.refresh(row)
    return row


@router.post("/scrims", status_code=status.HTTP_201_CREATED)
def create_scrim(
    payload: ScrimIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, payload.team_id, current_user)
    opponent = db.get(Team, payload.opponent_team_id) if payload.opponent_team_id else None
    if payload.opponent_team_id and not opponent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opponent team not found.")
    row = Scrim(
        created_by=current_user.id,
        opponent_name=opponent.name if opponent else (payload.opponent_name or "Open opponent slot"),
        **payload.model_dump(exclude={"opponent_name"}),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/scrims")
def list_scrims(
    mode: Mode | None = None,
    open_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Scrim).filter(Scrim.status == ScrimStatus.UPCOMING, Scrim.scheduled_at > utcnow())
    if mode:
        query = query.filter(Scrim.mode == mode)
    if open_only:
        query = query.filter(Scrim.is_open.is_(True))
    return query.order_by(Scrim.scheduled_at.asc()).limit(limit).all()


@router.post("/scrims/{scrim_id}/claim")
def claim_scrim(
    scrim_id: uuid.UUID,
    payload: ScrimClaimIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(Scrim).filter(Scrim.id == scrim_id).with_for_update().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scrim not found.")
    opponent = require_team_manager(db, payload.opponent_team_id, current_user)
    if not row.is_open or row.opponent_team_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This scrim is no longer open.")
    if opponent.id == row.team_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A team cannot claim its own scrim.")
    row.opponent_team_id = opponent.id
    row.opponent_name = opponent.name
    row.is_open = False
    _notify_manager(db, row.team_id, "Scrim opponent found", f"{opponent.name} claimed your scrim slot.", f"/scrims/{row.id}")
    db.commit()
    db.refresh(row)
    return row


@router.patch("/scrims/{scrim_id}")
def update_scrim_status(
    scrim_id: uuid.UUID,
    payload: ScrimStatusIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(Scrim, scrim_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scrim not found.")
    require_team_manager(db, row.team_id, current_user)
    if row.status != ScrimStatus.UPCOMING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed or cancelled scrims cannot be changed.")
    row.status = payload.status
    db.commit()
    db.refresh(row)
    return row
