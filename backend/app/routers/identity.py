from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import Region
from app.schemas.identity import RegionOut


router = APIRouter(tags=["identity"])


@router.get("/regions", response_model=list[RegionOut])
def list_regions(
    zone: str | None = Query(default=None, min_length=2, max_length=50),
    db: Session = Depends(get_db),
):
    query = db.query(Region)
    if zone:
        query = query.filter(Region.zone.ilike(zone.strip()))
    return query.order_by(Region.zone.asc(), Region.name.asc()).all()
