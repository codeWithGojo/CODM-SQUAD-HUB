from __future__ import annotations

import itertools
import uuid

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.competitive import OfficialTeamResult
from app.models.enums import (
    BlacklistStatus,
    BlacklistSubjectType,
    MatchResult,
    RegistrationStatus,
    TournamentFormat,
    TournamentMatchStatus,
)
from app.models.governance import BlacklistEntry
from app.models.team import Team
from app.models.tournament import Tournament, TournamentMatch, TournamentRegistration, TournamentStanding


def active_blacklist_entries(db: Session, subject_type: BlacklistSubjectType, subject_ids: list[uuid.UUID]):
    if not subject_ids:
        return []
    now = utcnow()
    return (
        db.query(BlacklistEntry)
        .filter(
            BlacklistEntry.subject_type == subject_type,
            BlacklistEntry.subject_id.in_(subject_ids),
            BlacklistEntry.status.in_([BlacklistStatus.ACTIVE, BlacklistStatus.APPEALED]),
            BlacklistEntry.starts_at <= now,
            or_(BlacklistEntry.ends_at.is_(None), BlacklistEntry.ends_at > now),
        )
        .all()
    )


def assert_registration_eligible(
    db: Session,
    *,
    team: Team,
    roster_user_ids: list[uuid.UUID],
) -> None:
    entries = active_blacklist_entries(db, BlacklistSubjectType.TEAM, [team.id])
    if team.organization_id:
        entries.extend(active_blacklist_entries(db, BlacklistSubjectType.ORGANIZATION, [team.organization_id]))
    entries.extend(active_blacklist_entries(db, BlacklistSubjectType.USER, roster_user_ids))
    blocking = [entry for entry in entries if entry.sanction_type.value in {"tournament_ban", "platform_ban"}]
    if blocking:
        names = ", ".join(sorted({entry.subject_name_snapshot for entry in blocking}))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Registration blocked by an active CRA sanction: {names}.",
        )


def generate_bracket(db: Session, tournament: Tournament, *, reset: bool = False) -> list[TournamentMatch]:
    existing = db.query(TournamentMatch).filter(TournamentMatch.tournament_id == tournament.id).count()
    if existing and not reset:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bracket already contains matches.")
    if existing and reset:
        db.query(TournamentMatch).filter(TournamentMatch.tournament_id == tournament.id).delete()

    registrations = (
        db.query(TournamentRegistration)
        .filter(
            TournamentRegistration.tournament_id == tournament.id,
            TournamentRegistration.status == RegistrationStatus.APPROVED,
        )
        .order_by(TournamentRegistration.seed.asc().nullslast(), TournamentRegistration.created_at.asc())
        .all()
    )
    if len(registrations) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least two approved teams are required.")

    team_ids = [row.team_id for row in registrations]
    matches: list[TournamentMatch] = []
    if tournament.format == TournamentFormat.ROUND_ROBIN:
        pairings = list(itertools.combinations(team_ids, 2))
        for position, (team_a, team_b) in enumerate(pairings, 1):
            matches.append(
                TournamentMatch(
                    tournament_id=tournament.id,
                    round_name="League",
                    bracket_position=position,
                    team_a_id=team_a,
                    team_b_id=team_b,
                )
            )
    else:
        pairings: list[tuple[uuid.UUID, uuid.UUID | None]] = []
        while team_ids:
            team_a = team_ids.pop(0)
            team_b = team_ids.pop(-1) if team_ids else None
            pairings.append((team_a, team_b))
        for position, (team_a, team_b) in enumerate(pairings, 1):
            matches.append(
                TournamentMatch(
                    tournament_id=tournament.id,
                    round_name="Round 1",
                    bracket_position=position,
                    team_a_id=team_a,
                    team_b_id=team_b,
                    winner_team_id=team_a if team_b is None else None,
                    status=TournamentMatchStatus.VERIFIED if team_b is None else TournamentMatchStatus.SCHEDULED,
                    verified_at=utcnow() if team_b is None else None,
                )
            )
    db.add_all(matches)
    db.flush()
    tournament.bracket = {
        "format": tournament.format.value,
        "rounds": [{"name": "Round 1" if tournament.format != TournamentFormat.ROUND_ROBIN else "League", "match_ids": [str(row.id) for row in matches]}],
    }
    return matches


def verify_match_and_update_ledger(
    db: Session,
    *,
    match: TournamentMatch,
    verifier_id: uuid.UUID,
) -> None:
    if match.team_a_id is None or match.team_b_id is None or match.score_a is None or match.score_b is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both teams and both scores are required.")
    tournament = db.get(Tournament, match.tournament_id)
    if not tournament:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found.")

    match.status = TournamentMatchStatus.VERIFIED
    match.verified_by = verifier_id
    match.verified_at = utcnow()
    match.played_at = match.played_at or utcnow()
    match.winner_team_id = None if match.score_a == match.score_b else (match.team_a_id if match.score_a > match.score_b else match.team_b_id)

    db.query(OfficialTeamResult).filter(OfficialTeamResult.tournament_match_id == match.id).delete()
    result_a = MatchResult.DRAW if match.score_a == match.score_b else (MatchResult.WIN if match.score_a > match.score_b else MatchResult.LOSS)
    result_b = MatchResult.DRAW if match.score_a == match.score_b else (MatchResult.WIN if match.score_b > match.score_a else MatchResult.LOSS)
    db.add_all(
        [
            OfficialTeamResult(
                team_id=match.team_a_id,
                opponent_team_id=match.team_b_id,
                tournament_match_id=match.id,
                mode=tournament.mode,
                result=result_a,
                score_for=match.score_a,
                score_against=match.score_b,
                submitted_by=match.reported_by or verifier_id,
                is_verified=True,
                verified_by=verifier_id,
                verified_at=utcnow(),
                played_at=match.played_at,
            ),
            OfficialTeamResult(
                team_id=match.team_b_id,
                opponent_team_id=match.team_a_id,
                tournament_match_id=match.id,
                mode=tournament.mode,
                result=result_b,
                score_for=match.score_b,
                score_against=match.score_a,
                submitted_by=match.reported_by or verifier_id,
                is_verified=True,
                verified_by=verifier_id,
                verified_at=utcnow(),
                played_at=match.played_at,
            ),
        ]
    )
    _apply_standing(db, tournament.id, match.team_a_id, match.score_a, match.score_b)
    _apply_standing(db, tournament.id, match.team_b_id, match.score_b, match.score_a)


def _apply_standing(db: Session, tournament_id: uuid.UUID, team_id: uuid.UUID, score_for: int, score_against: int) -> None:
    row = db.query(TournamentStanding).filter_by(tournament_id=tournament_id, team_id=team_id).first()
    if not row:
        row = TournamentStanding(
            tournament_id=tournament_id,
            team_id=team_id,
            played=0,
            wins=0,
            losses=0,
            draws=0,
            points=0,
            score_for=0,
            score_against=0,
        )
        db.add(row)
    row.played += 1
    row.score_for += score_for
    row.score_against += score_against
    if score_for > score_against:
        row.wins += 1
        row.points += 3
    elif score_for < score_against:
        row.losses += 1
    else:
        row.draws += 1
        row.points += 1
