from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_platform_admin
from app.core.time import utcnow
from app.models.enums import TournamentOrganizerStatus
from app.models.organizer import TournamentOrganizerApplication
from app.models.user import User
from app.schemas.organizers import ApplyOrganizerIn, OrganizerApplicationOut, ReviewOrganizerIn

router = APIRouter(prefix="/organizer-applications", tags=["tournament-organizers"])


@router.post("", response_model=OrganizerApplicationOut, status_code=status.HTTP_201_CREATED)
def apply_to_be_organizer(
    payload: ApplyOrganizerIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(TournamentOrganizerApplication).filter_by(user_id=current_user.id).first()
    if existing:
        if existing.status in {TournamentOrganizerStatus.REJECTED, TournamentOrganizerStatus.SUSPENDED}:
            existing.status = TournamentOrganizerStatus.PENDING
            existing.reason_for_applying = payload.reason_for_applying
            existing.experience_summary = payload.experience_summary
            existing.review_note = None
            existing.reviewed_by = None
            existing.reviewed_at = None
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Application already exists ({existing.status.value}).")
    row = TournamentOrganizerApplication(user_id=current_user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/me", response_model=OrganizerApplicationOut)
def my_application(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(TournamentOrganizerApplication).filter_by(user_id=current_user.id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No organizer application found.")
    return row


@router.get("", response_model=list[OrganizerApplicationOut])
def list_applications(
    application_status: TournamentOrganizerStatus | None = Query(default=None, alias="status"),
    _admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    query = db.query(TournamentOrganizerApplication)
    if application_status:
        query = query.filter(TournamentOrganizerApplication.status == application_status)
    return query.order_by(TournamentOrganizerApplication.created_at.desc()).limit(200).all()


@router.patch("/{application_id}", response_model=OrganizerApplicationOut)
def review_application(
    application_id: uuid.UUID,
    payload: ReviewOrganizerIn,
    admin: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    if payload.status == TournamentOrganizerStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review must approve, reject, or suspend.")
    row = db.get(TournamentOrganizerApplication, application_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    row.status = payload.status
    row.review_note = payload.review_note
    row.reviewed_by = admin.id
    row.reviewed_at = utcnow()
    db.commit()
    db.refresh(row)
    return row
