from __future__ import annotations

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import RankingEntityType
from app.models.organization_extra import Achievement
from app.models.ranking import RankingSnapshot
from app.models.tournament import TournamentPlayerStat
from app.models.transfer import MarketValueSnapshot
from app.models.user import User


def compute_market_value(
    db: Session,
    *,
    player_id: uuid.UUID,
    trigger_type: str = "manual",
    trigger_id: uuid.UUID | None = None,
) -> MarketValueSnapshot:
    """Produce an explainable estimate from verified platform signals only."""
    player = db.get(User, player_id)
    if not player:
        raise ValueError("Player not found")

    ranking = (
        db.query(RankingSnapshot)
        .filter(
            RankingSnapshot.entity_type == RankingEntityType.PLAYER,
            RankingSnapshot.entity_id == player_id,
            RankingSnapshot.is_current.is_(True),
        )
        .order_by(RankingSnapshot.rating.desc())
        .first()
    )
    totals = (
        db.query(
            func.count(TournamentPlayerStat.id),
            func.coalesce(func.sum(TournamentPlayerStat.kills), 0),
            func.coalesce(func.sum(TournamentPlayerStat.deaths), 0),
            func.coalesce(func.sum(TournamentPlayerStat.assists), 0),
            func.coalesce(func.sum(TournamentPlayerStat.damage), 0),
            func.coalesce(func.sum(TournamentPlayerStat.is_mvp), 0),
        )
        .filter(TournamentPlayerStat.user_id == player_id)
        .one()
    )
    matches, kills, deaths, assists, damage, mvps = (int(value or 0) for value in totals)
    verified_achievements = (
        db.query(Achievement.id)
        .filter(Achievement.user_id == player_id, Achievement.is_verified.is_(True))
        .count()
    )
    rating = float(ranking.rating) if ranking else 1000.0
    kd = round(kills / max(deaths, 1), 2)
    avg_damage = round(damage / max(matches, 1), 2)

    base = 100_000
    ranking_component = max(0, round((rating - 800) * 1_500))
    experience_component = min(matches, 100) * 12_500
    performance_component = min(round(kd * 225_000 + avg_damage * 10), 2_500_000)
    recognition_component = mvps * 150_000 + verified_achievements * 250_000
    reputation_component = max(0, player.reputation_score - 50) * 20_000
    estimated = min(
        100_000_000,
        max(
            100_000,
            base
            + ranking_component
            + experience_component
            + performance_component
            + recognition_component
            + reputation_component,
        ),
    )
    factors = {
        "formula_version": "verified-signals-v1",
        "rating": rating,
        "matches": matches,
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kd": kd,
        "average_damage": avg_damage,
        "mvps": mvps,
        "verified_achievements": verified_achievements,
        "reputation": player.reputation_score,
        "components_naira": {
            "base": base,
            "ranking": ranking_component,
            "experience": experience_component,
            "performance": performance_component,
            "recognition": recognition_component,
            "reputation": reputation_component,
        },
        "disclaimer": "Estimate only; it is not a mandated transfer fee.",
    }
    row = MarketValueSnapshot(
        player_id=player_id,
        estimated_value_naira=estimated,
        factors=factors,
        trigger_type=trigger_type,
        trigger_id=trigger_id,
    )
    db.add(row)
    return row
