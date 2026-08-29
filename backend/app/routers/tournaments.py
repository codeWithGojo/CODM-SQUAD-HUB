from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_platform_admin, require_tournament_organizer
from app.core.time import as_utc, utcnow
from app.models.enums import (
    BlacklistStatus,
    BlacklistSubjectType,
    CareerStatus,
    DisputeStatus,
    Mode,
    RegistrationStatus,
    TournamentMatchStatus,
    TournamentStatus,
)
from app.models.governance import BlacklistAppeal, BlacklistEntry, TournamentDispute
from app.models.ranking import Season
from app.models.team import Organization, Team, TeamMember
from app.models.tournament import (
    Tournament,
    TournamentMatch,
    TournamentPlayerStat,
    TournamentRegistration,
    TournamentStanding,
)
from app.models.user import User
from app.schemas.tournaments import (
    BlacklistAppealDecisionIn,
    BlacklistAppealIn,
    BlacklistEntryIn,
    BlacklistEntryOut,
    BlacklistRevokeIn,
    DisputeIn,
    DisputeRulingIn,
    GenerateBracketIn,
    MatchCreateIn,
    MatchOut,
    MatchReportIn,
    PlayerStatIn,
    RegistrationIn,
    RegistrationOut,
    RegistrationReviewIn,
    TournamentCreateIn,
    TournamentOut,
    TournamentUpdateIn,
)
from app.services.permissions import get_team_or_404, require_team_manager
from app.services.permissions import require_org_permission
from app.services.market_value import compute_market_value
from app.services.rankings import calculate_rankings
from app.services.realtime import realtime
from app.services.tournaments import assert_registration_eligible, generate_bracket, verify_match_and_update_ledger

router = APIRouter(prefix="/tournaments", tags=["tournaments"])
governance_router = APIRouter(prefix="/governance", tags=["competitive-integrity"])


def _require_tournament_owner(tournament: Tournament, user: User) -> None:
    if not user.is_platform_admin and tournament.organizer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only this tournament's organizer can do that.")


@router.get("", response_model=list[TournamentOut])
def list_tournaments(
    tournament_status: TournamentStatus | None = Query(default=None, alias="status"),
    mode: Mode | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Tournament)
    if tournament_status:
        query = query.filter(Tournament.status == tournament_status)
    else:
        query = query.filter(Tournament.status != TournamentStatus.DRAFT)
    if mode:
        query = query.filter(Tournament.mode == mode)
    return query.order_by(Tournament.starts_at.asc(), Tournament.id.asc()).limit(limit).all()


@router.post("", response_model=TournamentOut, status_code=status.HTTP_201_CREATED)
def create_tournament(
    payload: TournamentCreateIn,
    organizer: User = Depends(require_tournament_organizer),
    db: Session = Depends(get_db),
):
    if db.query(Tournament.id).filter(Tournament.slug == payload.slug).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tournament slug already exists.")
    if payload.season_id and not db.get(Season, payload.season_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown season_id.")
    row = Tournament(organizer_id=organizer.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{tournament_id}", response_model=TournamentOut)
def get_tournament(tournament_id: uuid.UUID, db: Session = Depends(get_db)):
    row = db.get(Tournament, tournament_id)
    if not row or row.status == TournamentStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found.")
    return row


@router.patch("/{tournament_id}", response_model=TournamentOut)
def update_tournament(
    tournament_id: uuid.UUID,
    payload: TournamentUpdateIn,
    background_tasks: BackgroundTasks,
    organizer: User = Depends(require_tournament_organizer),
    db: Session = Depends(get_db),
):
    row = db.get(Tournament, tournament_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found.")
    _require_tournament_owner(row, organizer)
    if payload.status and payload.status != row.status:
        allowed = {
            TournamentStatus.DRAFT: {TournamentStatus.REGISTRATION, TournamentStatus.CANCELLED},
            TournamentStatus.REGISTRATION: {TournamentStatus.ROSTER_LOCKED, TournamentStatus.CANCELLED},
            TournamentStatus.ROSTER_LOCKED: {TournamentStatus.LIVE, TournamentStatus.CANCELLED},
            TournamentStatus.LIVE: {TournamentStatus.COMPLETED, TournamentStatus.CANCELLED},
            TournamentStatus.COMPLETED: {TournamentStatus.ARCHIVED},
            TournamentStatus.CANCELLED: {TournamentStatus.ARCHIVED},
            TournamentStatus.ARCHIVED: set(),
        }
        if payload.status not in allowed[row.status]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tournament cannot move from {row.status.value} to {payload.status.value}.",
            )
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    if payload.status == TournamentStatus.REGISTRATION and row.published_at is None:
        row.published_at = utcnow()
    if payload.status == TournamentStatus.COMPLETED:
        row.completed_at = utcnow()
        if row.season_id:
            season = db.get(Season, row.season_id)
            if season:
                calculate_rankings(db, season=season, mode=row.mode, triggered_by=organizer.id)
    db.commit()
    db.refresh(row)
    background_tasks.add_task(
        realtime.publish_channel,
        f"tournament:{row.id}",
        {"type": "tournament.updated", "tournament_id": str(row.id), "status": row.status.value},
    )
    return row


@router.post("/{tournament_id}/registrations", response_model=RegistrationOut, status_code=status.HTTP_201_CREATED)
def register_team(
    tournament_id: uuid.UUID,
    payload: RegistrationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).with_for_update().first()
    if not tournament or tournament.status != TournamentStatus.REGISTRATION:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tournament registration is not open.")
    if tournament.registration_opens_at and as_utc(tournament.registration_opens_at) > utcnow():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Registration has not opened yet.")
    if tournament.registration_closes_at and as_utc(tournament.registration_closes_at) <= utcnow():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Registration has closed.")
    if tournament.roster_lock_at and as_utc(tournament.roster_lock_at) <= utcnow():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tournament rosters are locked.")
    team = require_team_manager(db, payload.team_id, current_user)
    roster_ids = list(dict.fromkeys(payload.roster_user_ids))
    stand_in_ids = list(dict.fromkeys(payload.stand_in_user_ids))
    if set(roster_ids) & set(stand_in_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A player cannot be both rostered and a stand-in.")
    if not tournament.min_roster_size <= len(roster_ids) <= tournament.max_roster_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Roster must contain {tournament.min_roster_size}–{tournament.max_roster_size} players.",
        )
    active_ids = {
        row[0]
        for row in db.query(TeamMember.user_id)
        .filter(TeamMember.team_id == team.id, TeamMember.user_id.in_(roster_ids), TeamMember.is_active.is_(True))
        .all()
    }
    if active_ids != set(roster_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Every roster player must be an active team member.")
    all_player_ids = roster_ids + stand_in_ids
    players = db.query(User).filter(User.id.in_(all_player_ids)).all()
    if len(players) != len(all_player_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more registered players do not exist.")
    if any(
        player.career_status != CareerStatus.ACTIVE
        or (player.is_banned and (player.banned_until is None or as_utc(player.banned_until) > utcnow()))
        for player in players
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive or banned players cannot be registered.")
    if any(not player.is_adult and not player.parental_consent_confirmed for player in players):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Every minor requires confirmed parental consent.")
    assert_registration_eligible(db, team=team, roster_user_ids=all_player_ids)
    occupied = (
        db.query(TournamentRegistration.id)
        .filter(
            TournamentRegistration.tournament_id == tournament.id,
            TournamentRegistration.status.in_([RegistrationStatus.PENDING, RegistrationStatus.APPROVED]),
        )
        .count()
    )
    if occupied >= tournament.max_teams:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tournament registration is full.")
    row = TournamentRegistration(
        tournament_id=tournament.id,
        team_id=team.id,
        submitted_by=current_user.id,
        roster_user_ids=[str(value) for value in roster_ids],
        stand_in_user_ids=[str(value) for value in stand_in_ids],
    )
    db.add(row)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Team is already registered.") from exc
    db.refresh(row)
    return row


@router.get("/{tournament_id}/registrations", response_model=list[RegistrationOut])
def list_registrations(tournament_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(TournamentRegistration).filter_by(tournament_id=tournament_id).order_by(TournamentRegistration.created_at.asc()).all()


@router.patch("/{tournament_id}/registrations/{registration_id}", response_model=RegistrationOut)
def review_registration(
    tournament_id: uuid.UUID,
    registration_id: uuid.UUID,
    payload: RegistrationReviewIn,
    organizer: User = Depends(require_tournament_organizer),
    db: Session = Depends(get_db),
):
    tournament = db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found.")
    _require_tournament_owner(tournament, organizer)
    row = db.get(TournamentRegistration, registration_id)
    if not row or row.tournament_id != tournament_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found.")
    if payload.status == RegistrationStatus.APPROVED and row.status != RegistrationStatus.APPROVED:
        approved = (
            db.query(TournamentRegistration.id)
            .filter_by(tournament_id=tournament_id, status=RegistrationStatus.APPROVED)
            .count()
        )
        if approved >= tournament.max_teams:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tournament has reached its approved-team limit.")
    row.status = payload.status
    row.seed = payload.seed
    row.review_note = payload.review_note
    row.reviewed_by = organizer.id
    row.reviewed_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


@router.post("/{tournament_id}/bracket", response_model=list[MatchOut])
def build_bracket(
    tournament_id: uuid.UUID,
    payload: GenerateBracketIn,
    background_tasks: BackgroundTasks,
    organizer: User = Depends(require_tournament_organizer),
    db: Session = Depends(get_db),
):
    tournament = db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found.")
    _require_tournament_owner(tournament, organizer)
    rows = generate_bracket(db, tournament, reset=payload.reset_existing)
    db.commit()
    background_tasks.add_task(
        realtime.publish_channel,
        f"tournament:{tournament.id}",
        {"type": "bracket.generated", "tournament_id": str(tournament.id), "match_count": len(rows)},
    )
    return rows


@router.post("/{tournament_id}/matches", response_model=MatchOut, status_code=status.HTTP_201_CREATED)
def create_match(
    tournament_id: uuid.UUID,
    payload: MatchCreateIn,
    organizer: User = Depends(require_tournament_organizer),
    db: Session = Depends(get_db),
):
    tournament = db.get(Tournament, tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found.")
    _require_tournament_owner(tournament, organizer)
    team_ids = [value for value in (payload.team_a_id, payload.team_b_id) if value]
    if len(team_ids) != len(set(team_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A team cannot play itself.")
    if team_ids:
        approved_ids = {
            value[0]
            for value in db.query(TournamentRegistration.team_id)
            .filter(
                TournamentRegistration.tournament_id == tournament_id,
                TournamentRegistration.team_id.in_(team_ids),
                TournamentRegistration.status == RegistrationStatus.APPROVED,
            )
            .all()
        }
        if approved_ids != set(team_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Every match team must have an approved registration.")
    row = TournamentMatch(tournament_id=tournament_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{tournament_id}/matches", response_model=list[MatchOut])
def list_matches(tournament_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(TournamentMatch).filter_by(tournament_id=tournament_id).order_by(TournamentMatch.bracket_position.asc()).all()


@router.post("/{tournament_id}/matches/{match_id}/report", response_model=MatchOut)
def report_match(
    tournament_id: uuid.UUID,
    match_id: uuid.UUID,
    payload: MatchReportIn,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match = db.get(TournamentMatch, match_id)
    if not match or match.tournament_id != tournament_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")
    if match.status == TournamentMatchStatus.VERIFIED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Verified matches cannot be changed.")
    managed = []
    for team_id in [match.team_a_id, match.team_b_id]:
        if team_id:
            try:
                require_team_manager(db, team_id, current_user)
                managed.append(team_id)
            except HTTPException:
                pass
    if not managed and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A participating team manager must report the score.")
    match.score_a = payload.score_a
    match.score_b = payload.score_b
    match.map_scores = payload.map_scores
    match.proof_urls = payload.proof_urls
    match.played_at = payload.played_at or utcnow()
    match.reported_by = current_user.id
    match.status = TournamentMatchStatus.REPORTED
    db.commit()
    db.refresh(match)
    background_tasks.add_task(
        realtime.publish_channel,
        f"tournament:{tournament_id}",
        {"type": "match.reported", "match_id": str(match.id), "score_a": match.score_a, "score_b": match.score_b},
    )
    return match
