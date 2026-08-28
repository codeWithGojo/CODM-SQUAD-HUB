from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_tournament_organizer
from app.models.enums import Mode, RankingEntityType, RankingScope
from app.models.ranking import RankingSnapshot, Season
from app.models.user import User
from app.schemas.rankings import RankingSnapshotOut, RecalculateRankingsIn, SeasonIn, SeasonOut
from app.services.rankings import BASE_K, BASE_TEAM_RATING, FORMULA_VERSION, RECENCY_HALF_LIFE_DAYS, calculate_rankings
from app.services.realtime import realtime

router = APIRouter(tags=["rankings"])


@router.get("/seasons", response_model=list[SeasonOut])
def list_seasons(db: Session = Depends(get_db)):
    return db.query(Season).order_by(Season.starts_on.desc()).all()


@router.post("/seasons", response_model=SeasonOut, status_code=status.HTTP_201_CREATED)
def create_season(
    payload: SeasonIn,
    organizer: User = Depends(require_tournament_organizer),
    db: Session = Depends(get_db),
):
    if db.query(Season.id).filter(Season.code == payload.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Season code already exists.")
    if payload.is_active:
        db.query(Season).update({"is_active": False})
    row = Season(created_by=organizer.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/rankings/recalculate", status_code=status.HTTP_202_ACCEPTED)
def recalculate_rankings(
    payload: RecalculateRankingsIn,
    background_tasks: BackgroundTasks,
    organizer: User = Depends(require_tournament_organizer),
    db: Session = Depends(get_db),
):
    season = db.get(Season, payload.season_id)
    if not season:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found.")
    calculation = calculate_rankings(db, season=season, mode=payload.mode, triggered_by=organizer.id)
    db.commit()
    background_tasks.add_task(
        realtime.publish_channel,
        f"rankings:{season.id}:{payload.mode.value}",
        {"type": "rankings.updated", "calculation_id": str(calculation.id), "mode": payload.mode.value},
    )
    return {"calculation_id": calculation.id, "source_match_count": calculation.source_match_count, "status": "completed"}


@router.get("/rankings", response_model=list[RankingSnapshotOut])
def ranking_table(
    season_id: uuid.UUID,
    mode: Mode,
    entity_type: RankingEntityType = RankingEntityType.TEAM,
    scope: RankingScope = RankingScope.CONTINENTAL,
    scope_code: str = "AFRICA",
    after_rank: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(RankingSnapshot)
        .filter(
            RankingSnapshot.season_id == season_id,
            RankingSnapshot.mode == mode,
            RankingSnapshot.entity_type == entity_type,
            RankingSnapshot.scope == scope,
            RankingSnapshot.scope_code == scope_code,
            RankingSnapshot.is_current.is_(True),
            RankingSnapshot.rank > after_rank,
        )
        .order_by(RankingSnapshot.rank.asc())
        .limit(limit)
        .all()
    )


@router.get("/rankings/{entity_type}/{entity_id}/history", response_model=list[RankingSnapshotOut])
def ranking_history(
    entity_type: RankingEntityType,
    entity_id: uuid.UUID,
    mode: Mode | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(RankingSnapshot).filter(
        RankingSnapshot.entity_type == entity_type,
        RankingSnapshot.entity_id == entity_id,
    )
    if mode:
        query = query.filter(RankingSnapshot.mode == mode)
    return query.order_by(RankingSnapshot.generated_at.desc()).limit(limit).all()


@router.get("/rankings/formula")
def ranking_formula():
    return {
        "version": FORMULA_VERSION,
        "team_base_rating": BASE_TEAM_RATING,
        "elo_k": BASE_K,
        "recency_half_life_days": RECENCY_HALF_LIFE_DAYS,
        "factors": ["verified result", "opponent strength", "event weight", "stage", "recency"],
        "separation": "MP and BR are calculated independently; national, regional and Africa tables share the same ledger.",
    }
