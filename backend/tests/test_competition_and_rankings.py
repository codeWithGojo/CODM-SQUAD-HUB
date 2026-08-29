from __future__ import annotations

from datetime import date, timedelta
import uuid

from app.models.competitive import OfficialTeamResult
from app.models.ranking import RankingSnapshot
from tests.conftest import auth


def test_confirmed_challenge_enters_official_ranking_ledger(client, db, seed):
    created = client.post(
        "/api/v1/challenges",
        headers=auth(seed["manager_a"]),
        json={
            "challenger_team_id": str(seed["team_a"].id),
            "challenged_team_id": str(seed["team_b"].id),
            "mode": "MP",
            "format": "BO5",
        },
    )
    assert created.status_code == 201
    challenge_id = uuid.UUID(created.json()["id"])
    assert client.post(f"/api/v1/challenges/{challenge_id}/respond", headers=auth(seed["manager_b"]), json={"accept": True}).status_code == 200
    reported = client.post(
        f"/api/v1/challenges/{challenge_id}/result",
        headers=auth(seed["manager_a"]),
        json={
            "score_challenger": 3,
            "score_challenged": 1,
            "score_details": {"maps": ["Raid", "Standoff"]},
            "proof_screenshot_url": "https://example.com/proof.png",
        },
    )
    assert reported.status_code == 200
    confirmed = client.post(
        f"/api/v1/challenges/{challenge_id}/confirm",
        headers=auth(seed["manager_b"]),
        json={"confirm": True},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "completed"
    assert db.query(OfficialTeamResult).filter_by(challenge_id=challenge_id, is_verified=True).count() == 2

    today = date.today()
    season = client.post(
        "/api/v1/seasons",
        headers=auth(seed["organizer"]),
        json={
            "name": "Pilot Season",
            "code": "PILOT_1",
            "starts_on": str(today - timedelta(days=30)),
            "ends_on": str(today + timedelta(days=30)),
            "is_active": True,
        },
    )
    assert season.status_code == 201
    recalculated = client.post(
        "/api/v1/rankings/recalculate",
        headers=auth(seed["organizer"]),
        json={"season_id": season.json()["id"], "mode": "MP"},
    )
    assert recalculated.status_code == 202
    assert recalculated.json()["source_match_count"] == 1
    assert db.query(RankingSnapshot).filter_by(scope_code="AFRICA", is_current=True).count() == 2


def test_scrim_finder_claim_is_atomic(client, seed):
    created = client.post(
        "/api/v1/scrims",
        headers=auth(seed["manager_a"]),
        json={
            "team_id": str(seed["team_a"].id),
            "mode": "MP",
            "format": "BO5",
            "scheduled_at": "2027-01-01T18:00:00Z",
            "is_open": True,
        },
    )
    assert created.status_code == 201
    claimed = client.post(
        f"/api/v1/scrims/{created.json()['id']}/claim",
        headers=auth(seed["manager_b"]),
        json={"opponent_team_id": str(seed["team_b"].id)},
    )
    assert claimed.status_code == 200
    assert claimed.json()["is_open"] is False
    second = client.post(
        f"/api/v1/scrims/{created.json()['id']}/claim",
        headers=auth(seed["manager_b"]),
        json={"opponent_team_id": str(seed["team_b"].id)},
    )
    assert second.status_code == 409
