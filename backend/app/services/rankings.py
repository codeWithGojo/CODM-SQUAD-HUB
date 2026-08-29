from __future__ import annotations

import math
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.competitive import Challenge, OfficialTeamResult
from app.models.enums import MatchResult, Mode, RankingEntityType, RankingScope, TournamentMatchStatus
from app.models.ranking import RankingCalculation, RankingSnapshot, Season
from app.models.team import Organization, Team
from app.models.tournament import Tournament, TournamentMatch, TournamentPlayerStat
from app.models.user import Region, User

FORMULA_VERSION = "elo-v1"
BASE_TEAM_RATING = 1500.0
BASE_PLAYER_RATING = 1000.0
BASE_K = 32.0
RECENCY_HALF_LIFE_DAYS = 180.0


@dataclass
class RatingState:
    rating: float
    matches: int = 0
    wins: int = 0
    losses: int = 0
    weighted_delta: float = 0.0


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def recency_multiplier(played_at: datetime, as_of: datetime) -> float:
    if played_at.tzinfo is None:
        played_at = played_at.replace(tzinfo=UTC)
    age_days = max(0.0, (as_of - played_at).total_seconds() / 86400.0)
    return max(0.20, 0.5 ** (age_days / RECENCY_HALF_LIFE_DAYS))


def stage_multiplier(round_name: str) -> float:
    value = round_name.lower()
    if "final" in value and "semi" not in value:
        return 1.25
    if "semi" in value:
        return 1.12
    if "quarter" in value:
        return 1.06
    return 1.0


def calculate_rankings(
    db: Session,
    *,
    season: Season,
    mode: Mode,
    triggered_by: uuid.UUID,
) -> RankingCalculation:
    calculation = RankingCalculation(
        season_id=season.id,
        mode=mode,
        formula_version=FORMULA_VERSION,
        triggered_by=triggered_by,
    )
    db.add(calculation)
    db.flush()

    start = datetime.combine(season.starts_on, time.min, tzinfo=UTC)
    end = datetime.combine(season.ends_on + timedelta(days=1), time.min, tzinfo=UTC)
    matches = (
        db.query(TournamentMatch, Tournament)
        .join(Tournament, Tournament.id == TournamentMatch.tournament_id)
        .filter(
            Tournament.season_id == season.id,
            Tournament.mode == mode,
            TournamentMatch.status == TournamentMatchStatus.VERIFIED,
            TournamentMatch.played_at >= start,
            TournamentMatch.played_at < end,
            TournamentMatch.team_a_id.is_not(None),
            TournamentMatch.team_b_id.is_not(None),
        )
        .order_by(TournamentMatch.played_at.asc(), TournamentMatch.id.asc())
        .all()
    )
    challenge_results = (
        db.query(OfficialTeamResult)
        .join(Challenge, Challenge.id == OfficialTeamResult.challenge_id)
        .filter(
            OfficialTeamResult.is_verified.is_(True),
            OfficialTeamResult.mode == mode,
            OfficialTeamResult.played_at >= start,
            OfficialTeamResult.played_at < end,
            OfficialTeamResult.team_id == Challenge.challenger_team_id,
        )
        .order_by(OfficialTeamResult.played_at.asc(), OfficialTeamResult.id.asc())
        .all()
    )
    calculation.source_match_count = len(matches) + len(challenge_results)
    as_of = min(utcnow(), end)
    team_states: dict[uuid.UUID, RatingState] = defaultdict(lambda: RatingState(BASE_TEAM_RATING))

    for match, tournament in matches:
        state_a = team_states[match.team_a_id]
        state_b = team_states[match.team_b_id]
        actual_a = 0.5 if match.score_a == match.score_b else (1.0 if match.score_a > match.score_b else 0.0)
        actual_b = 1.0 - actual_a
        expected_a = expected_score(state_a.rating, state_b.rating)
        weight = float(tournament.ranking_weight) * stage_multiplier(match.round_name)
        recency = recency_multiplier(match.played_at, as_of)
        delta = BASE_K * weight * recency * (actual_a - expected_a)
        state_a.rating += delta
        state_b.rating -= delta
        state_a.weighted_delta += delta
        state_b.weighted_delta -= delta
        state_a.matches += 1
        state_b.matches += 1
        if actual_a == 1:
            state_a.wins += 1
            state_b.losses += 1
        elif actual_b == 1:
            state_b.wins += 1
            state_a.losses += 1

    for result in challenge_results:
        if not result.opponent_team_id:
            continue
        state_a = team_states[result.team_id]
        state_b = team_states[result.opponent_team_id]
        actual_a = 0.5 if result.result == MatchResult.DRAW else (1.0 if result.result == MatchResult.WIN else 0.0)
        actual_b = 1.0 - actual_a
        expected_a = expected_score(state_a.rating, state_b.rating)
        delta = BASE_K * 0.5 * recency_multiplier(result.played_at, as_of) * (actual_a - expected_a)
        state_a.rating += delta
        state_b.rating -= delta
        state_a.weighted_delta += delta
        state_b.weighted_delta -= delta
        state_a.matches += 1
        state_b.matches += 1
        if actual_a == 1:
            state_a.wins += 1
            state_b.losses += 1
        elif actual_b == 1:
            state_b.wins += 1
            state_a.losses += 1

    team_ids = list(team_states)
    teams = {row.id: row for row in db.query(Team).filter(Team.id.in_(team_ids)).all()} if team_ids else {}
    region_ids = {team.region_id for team in teams.values()}
    regions = {row.id: row for row in db.query(Region).filter(Region.id.in_(region_ids)).all()} if region_ids else {}

    _replace_current_snapshots(
        db,
        calculation=calculation,
        season=season,
        mode=mode,
        entity_type=RankingEntityType.TEAM,
        rows=_team_rows(team_states, teams, regions),
    )

    player_rows = _calculate_player_rows(db, matches, team_states, regions)
    _replace_current_snapshots(
        db,
        calculation=calculation,
        season=season,
        mode=mode,
        entity_type=RankingEntityType.PLAYER,
        rows=player_rows,
    )

    org_rows = _organization_rows(db, team_states, teams)
    _replace_current_snapshots(
        db,
        calculation=calculation,
        season=season,
        mode=mode,
        entity_type=RankingEntityType.ORGANIZATION,
        rows=org_rows,
    )

    calculation.completed_at = utcnow()
    return calculation


def _team_rows(states: dict[uuid.UUID, RatingState], teams: dict[uuid.UUID, Team], regions: dict[uuid.UUID, Region]) -> list[dict]:
    rows: list[dict] = []
    for team_id, state in states.items():
        team = teams.get(team_id)
        if not team:
            continue
        region = regions.get(team.region_id)
        country = region.code if region else "UNASSIGNED"
        zone = region.zone if region else "UNASSIGNED"
        rows.append(
            {
                "entity_id": team.id,
                "entity_name": team.name,
                "rating": state.rating,
                "points": max(0.0, state.rating - 1000.0),
                "matches_played": state.matches,
                "wins": state.wins,
                "losses": state.losses,
                "country_code": country,
                "region_code": zone,
                "explanation": {
                    "base_rating": BASE_TEAM_RATING,
                    "weighted_delta": round(state.weighted_delta, 2),
                    "verified_matches": state.matches,
                    "formula_version": FORMULA_VERSION,
                },
            }
        )
    return rows


def _calculate_player_rows(db: Session, matches, team_states: dict[uuid.UUID, RatingState], regions: dict[uuid.UUID, Region]) -> list[dict]:
    match_map = {match.id: (match, tournament) for match, tournament in matches}
    if not match_map:
        return []
    stats = db.query(TournamentPlayerStat).filter(TournamentPlayerStat.match_id.in_(list(match_map))).all()
    states: dict[uuid.UUID, RatingState] = defaultdict(lambda: RatingState(BASE_PLAYER_RATING))
    for stat in stats:
        match, tournament = match_map[stat.match_id]
        state = states[stat.user_id]
        won = match.winner_team_id == stat.team_id
        raw = (
            stat.kills * 2.0
            + stat.assists * 0.75
            - stat.deaths * 1.5
            + float(stat.objective_score) * 0.02
            + (15.0 if stat.is_mvp else 0.0)
            + (10.0 if won else 0.0)
        )
        contribution = max(-20.0, min(50.0, raw - 20.0)) * float(tournament.ranking_weight)
        state.rating += contribution
        state.weighted_delta += contribution
        state.matches += 1
        if won:
            state.wins += 1
        else:
            state.losses += 1

    users = {row.id: row for row in db.query(User).filter(User.id.in_(list(states))).all()} if states else {}
    rows: list[dict] = []
    for user_id, state in states.items():
        user = users.get(user_id)
        if not user:
            continue
        region = regions.get(user.region_id) or (db.get(Region, user.region_id) if user.region_id else None)
        rows.append(
            {
                "entity_id": user.id,
                "entity_name": user.gamertag,
                "rating": state.rating,
                "points": max(0.0, state.rating - 500.0),
                "matches_played": state.matches,
                "wins": state.wins,
                "losses": state.losses,
                "country_code": region.code if region else "UNASSIGNED",
                "region_code": region.zone if region else "UNASSIGNED",
                "explanation": {
                    "base_rating": BASE_PLAYER_RATING,
                    "verified_stat_lines": state.matches,
                    "performance_delta": round(state.weighted_delta, 2),
                    "formula_version": FORMULA_VERSION,
                },
            }
        )
    return rows


def _organization_rows(db: Session, states: dict[uuid.UUID, RatingState], teams: dict[uuid.UUID, Team]) -> list[dict]:
    grouped: dict[uuid.UUID, list[tuple[Team, RatingState]]] = defaultdict(list)
    for team_id, state in states.items():
        team = teams.get(team_id)
        if team and team.organization_id:
            grouped[team.organization_id].append((team, state))
    organizations = {
        row.id: row for row in db.query(Organization).filter(Organization.id.in_(list(grouped))).all()
    } if grouped else {}
    country_codes = {row.country_code for row in organizations.values() if row.country_code}
    country_regions = {
        row.code: row
        for row in db.query(Region).filter(Region.code.in_(country_codes)).all()
    } if country_codes else {}
    rows: list[dict] = []
    for org_id, values in grouped.items():
        ordered = sorted(values, key=lambda value: value[1].rating, reverse=True)
        top = ordered[:2]
        rating = sum(value.rating for _, value in top) / len(top)
        org = organizations.get(org_id)
        country_code = org.country_code if org and org.country_code else "UNASSIGNED"
        region = country_regions.get(country_code)
        rows.append(
            {
                "entity_id": org_id,
                "entity_name": org.name if org else str(org_id),
                "rating": rating,
                "points": max(0.0, rating - 1000.0),
                "matches_played": sum(value.matches for _, value in values),
                "wins": sum(value.wins for _, value in values),
                "losses": sum(value.losses for _, value in values),
                "country_code": country_code,
                "region_code": region.zone if region else "UNASSIGNED",
                "explanation": {
                    "method": "average_best_two_active_team_ratings",
                    "team_count": len(values),
                    "formula_version": FORMULA_VERSION,
                },
            }
        )
    return rows


def _replace_current_snapshots(
    db: Session,
    *,
    calculation: RankingCalculation,
    season: Season,
    mode: Mode,
    entity_type: RankingEntityType,
    rows: list[dict],
) -> None:
    previous = (
        db.query(RankingSnapshot)
        .filter(
            RankingSnapshot.season_id == season.id,
            RankingSnapshot.mode == mode,
            RankingSnapshot.entity_type == entity_type,
            RankingSnapshot.is_current.is_(True),
        )
        .all()
    )
    previous_ranks = {(row.entity_id, row.scope, row.scope_code): row.rank for row in previous}
    for row in previous:
        row.is_current = False

    scopes: list[tuple[RankingScope, str, str]] = []
    for item in rows:
        scopes.extend(
            [
                (RankingScope.NATIONAL, item["country_code"], "country_code"),
                (RankingScope.REGIONAL, item["region_code"], "region_code"),
                (RankingScope.CONTINENTAL, "AFRICA", "continent"),
            ]
        )
    for scope, scope_code, key in sorted(set(scopes), key=lambda value: (value[0].value, value[1])):
        if scope == RankingScope.CONTINENTAL:
            candidates = rows
        else:
            candidates = [row for row in rows if row[key] == scope_code]
        candidates = sorted(candidates, key=lambda row: (-row["rating"], str(row["entity_id"])))
        for rank, item in enumerate(candidates, 1):
            previous_rank = previous_ranks.get((item["entity_id"], scope, scope_code))
            db.add(
                RankingSnapshot(
                    calculation_id=calculation.id,
                    season_id=season.id,
                    mode=mode,
                    entity_type=entity_type,
                    entity_id=item["entity_id"],
                    entity_name=item["entity_name"],
                    scope=scope,
                    scope_code=scope_code,
                    rating=round(item["rating"], 2),
                    points=round(item["points"], 2),
                    rank=rank,
                    previous_rank=previous_rank,
                    movement=(previous_rank - rank) if previous_rank else 0,
                    matches_played=item["matches_played"],
                    wins=item["wins"],
                    losses=item["losses"],
                    explanation=item["explanation"],
                    is_current=True,
                )
            )
