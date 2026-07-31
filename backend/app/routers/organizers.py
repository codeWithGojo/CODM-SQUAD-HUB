import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.organizer import TournamentOrganizerApplication
from app.models.enums import TournamentOrganizerStatus
from app.schemas.organizer import ApplyOrganizerIn, ReviewOrganizerIn, OrganizerApplicationOut

router = APIRouter(prefix="/organizer-applications", tags=["tournament-organizer"])


@router.post("", response_model=OrganizerApplicationOut, status_code=status.HTTP_201_CREATED)
def apply_to_be_organizer(
    payload: ApplyOrganizerIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Anyone can apply (locked decision) — this just files the application, doesn't grant anything yet."""
    existing = (
        db.query(TournamentOrganizerApplication)
        .filter(TournamentOrganizerApplication.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"You already have an application (status: {existing.status.value}).")

    application = TournamentOrganizerApplication(
        user_id=current_user.id,
        reason_for_applying=payload.reason_for_applying,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("/me", response_model=OrganizerApplicationOut)
def my_application(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = (
        db.query(TournamentOrganizerApplication)
        .filter(TournamentOrganizerApplication.user_id == current_user.id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="You haven't applied yet.")
    return application


@router.post("/{application_id}/review", response_model=OrganizerApplicationOut)
def review_application(
    application_id: uuid.UUID,
    payload: ReviewOrganizerIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    TODO: this currently lets ANY authenticated user approve/reject
    applications — same class of gap as the old resolve-dispute endpoint
    used to have. Needs a real admin/superuser check before this is
    safe to expose publicly. Flagged clearly here, not forgotten.
    """
    application = db.query(TournamentOrganizerApplication).filter(TournamentOrganizerApplication.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    application.status = TournamentOrganizerStatus.APPROVED if payload.approve else TournamentOrganizerStatus.REJECTED
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(application)
    return application