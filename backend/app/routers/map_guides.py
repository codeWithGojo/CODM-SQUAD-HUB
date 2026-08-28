from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.enums import Mode
from app.models.misc import MapGuide
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.map_guides import MapGuideIn, MapGuideOut
from app.services.permissions import require_team_manager

router = APIRouter(prefix="/map-guides", tags=["map-guides"])


@router.get("", response_model=list[MapGuideOut])
def curated_guides(
    map_name: str | None = None,
    mode: Mode | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(MapGuide).filter(MapGuide.team_id.is_(None), MapGuide.is_curated.is_(True), MapGuide.is_active.is_(True))
    if map_name:
        query = query.filter(MapGuide.map_name.ilike(map_name))
    if mode:
        query = query.filter(MapGuide.mode == mode)
    return query.order_by(MapGuide.map_name.asc(), MapGuide.slot_number.asc()).limit(limit).all()


@router.get("/teams/{team_id}", response_model=list[MapGuideOut])
def team_guides(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    member = db.query(TeamMember.id).filter_by(team_id=team_id, user_id=current_user.id, is_active=True).first()
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    if not member and team.manager_id != current_user.id and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team membership required.")
    return db.query(MapGuide).filter_by(team_id=team_id, is_active=True).order_by(MapGuide.map_name, MapGuide.slot_number).all()


@router.post("", response_model=MapGuideOut, status_code=status.HTTP_201_CREATED)
def create_guide(
    payload: MapGuideIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.team_id:
        require_team_manager(db, payload.team_id, current_user)
        if payload.is_curated:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team-private guides cannot be curated public guides.")
    elif not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create curated public guides.")
    elif not payload.is_curated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Public guides must be curated.")
    existing = db.query(MapGuide.id).filter_by(
        team_id=payload.team_id,
        map_name=payload.map_name,
        mode=payload.mode,
        slot_number=payload.slot_number,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That map-guide slot is already used.")
    row = MapGuide(
        created_by=current_user.id,
        approved_by=current_user.id if payload.is_curated else None,
        **payload.model_dump(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/{guide_id}", response_model=MapGuideOut)
def update_guide(
    guide_id: uuid.UUID,
    payload: MapGuideIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(MapGuide, guide_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")
    if row.team_id:
        require_team_manager(db, row.team_id, current_user)
        if payload.team_id != row.team_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A guide cannot be moved to another team.")
        if payload.is_curated:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team-private guides cannot be curated public guides.")
    elif not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    elif payload.team_id is None and not payload.is_curated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Public guides must be curated.")
    duplicate = (
        db.query(MapGuide.id)
        .filter(
            MapGuide.id != row.id,
            MapGuide.team_id == payload.team_id if payload.team_id else MapGuide.team_id.is_(None),
            MapGuide.map_name == payload.map_name,
            MapGuide.mode == payload.mode,
            MapGuide.slot_number == payload.slot_number,
            MapGuide.is_active.is_(True),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That map-guide slot is already used.")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    if row.is_curated:
        row.approved_by = current_user.id
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guide(
    guide_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.get(MapGuide, guide_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found.")
    if row.team_id:
        require_team_manager(db, row.team_id, current_user)
    elif not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    row.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
