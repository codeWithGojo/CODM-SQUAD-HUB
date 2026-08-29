from __future__ import annotations

from datetime import date, timedelta
import uuid

from app.models.commerce import CampaignContribution, CrowdfundingCampaign, MerchProduct, PaymentTransaction
from app.models.enums import PaymentStatus
from app.models.organization_extra import Achievement
from app.models.ranking import RankingSnapshot
from app.models.tournament import TournamentStanding
from app.services.payments import mark_payment_success
from tests.conftest import auth


def _create_open_tournament(client, seed, *, slug: str):
    created = client.post(
        "/api/v1/tournaments",
        headers=auth(seed["organizer"]),
        json={
            "name": slug.replace("-", " ").title(),
            "slug": slug,
            "mode": "MP",
            "format": "single_elimination",
            "min_roster_size": 1,
            "max_roster_size": 4,
            "starts_at": "2027-10-01T18:00:00Z",
        },
    )
    assert created.status_code == 201
    opened = client.patch(
        f"/api/v1/tournaments/{created.json()['id']}",
        headers=auth(seed["organizer"]),
        json={"status": "registration"},
    )
    assert opened.status_code == 200
    return opened.json()


def test_tournament_registration_stats_verification_and_standings(client, db, seed):
    tournament = _create_open_tournament(client, seed, slug="integrity-cup")
    registrations = []
    for team_key, manager_key, roster_key in (
        ("team_a", "manager_a", "player"),
        ("team_b", "manager_b", "manager_b"),
    ):
        response = client.post(
            f"/api/v1/tournaments/{tournament['id']}/registrations",
            headers=auth(seed[manager_key]),
            json={
                "team_id": str(seed[team_key].id),
                "roster_user_ids": [str(seed[roster_key].id)],
            },
        )
        assert response.status_code == 201
        registrations.append(response.json())

    for position, registration in enumerate(registrations, 1):
        reviewed = client.patch(
            f"/api/v1/tournaments/{tournament['id']}/registrations/{registration['id']}",
            headers=auth(seed["organizer"]),
            json={"status": "approved", "seed": position},
        )
        assert reviewed.status_code == 200

    bracket = client.post(
        f"/api/v1/tournaments/{tournament['id']}/bracket",
        headers=auth(seed["organizer"]),
        json={"reset_existing": False},
    )
    assert bracket.status_code == 200
    match = bracket.json()[0]
    reported = client.post(
        f"/api/v1/tournaments/{tournament['id']}/matches/{match['id']}/report",
        headers=auth(seed["manager_a"]),
        json={"score_a": 3, "score_b": 1, "proof_urls": ["https://example.com/result.png"]},
    )
    assert reported.status_code == 200

    invalid_stats = client.put(
        f"/api/v1/tournaments/{tournament['id']}/matches/{match['id']}/stats",
        headers=auth(seed["manager_a"]),
        json=[{"user_id": str(seed["outsider"].id), "team_id": str(seed["team_a"].id), "kills": 99}],
    )
    assert invalid_stats.status_code == 400
    valid_stats = client.put(
        f"/api/v1/tournaments/{tournament['id']}/matches/{match['id']}/stats",
        headers=auth(seed["manager_a"]),
        json=[
            {
                "user_id": str(seed["player"].id),
                "team_id": str(seed["team_a"].id),
                "kills": 20,
                "deaths": 8,
                "assists": 7,
                "objective_score": 110,
                "is_mvp": True,
                "hill_output": {
                    "map_name": "Raid",
                    "hill_labels": ["P1", "P2", "P3", "P4", "P1"],
                    "kills_by_hill": [4, 3, 5, 2, 6],
                    "shared_scale": 12,
                    "role_profile": {
                        "objective_pressure": 88,
                        "trades": 84,
                        "survival": 72,
                        "kills": 79,
                        "objective": 94,
                        "consistency": 86,
                    },
                },
            }
        ],
    )
    assert valid_stats.status_code == 201
    private_hill_output = client.get(
        f"/api/v1/tournaments/{tournament['id']}/matches/{match['id']}/hill-output",
        headers=auth(seed["manager_a"]),
        params={"team_id": str(seed["team_a"].id)},
    )
    assert private_hill_output.status_code == 200
    assert private_hill_output.json()["players"][0]["summary"]["peak_kills"] == 6
    forbidden_hill_output = client.get(
        f"/api/v1/tournaments/{tournament['id']}/matches/{match['id']}/hill-output",
        headers=auth(seed["outsider"]),
        params={"team_id": str(seed["team_a"].id)},
    )
    assert forbidden_hill_output.status_code == 403
    verified = client.post(
        f"/api/v1/tournaments/{tournament['id']}/matches/{match['id']}/verify",
        headers=auth(seed["organizer"]),
    )
    assert verified.status_code == 200
    assert verified.json()["status"] == "verified"
    public_hill_output = client.get(
        f"/api/v1/tournaments/{tournament['id']}/matches/{match['id']}/hill-output",
        headers=auth(seed["outsider"]),
        params={"team_id": str(seed["team_a"].id)},
    )
    assert public_hill_output.status_code == 200
    assert public_hill_output.json()["players"][0]["hill_output"]["map_name"] == "Raid"
    assert db.query(TournamentStanding).filter_by(tournament_id=uuid.UUID(tournament["id"])).count() == 2


def test_cra_blacklist_blocks_registration_and_supports_appeal(client, seed):
    sanction = client.post(
        "/api/v1/governance/blacklist",
        headers=auth(seed["admin"]),
        json={
            "subject_type": "team",
            "subject_id": str(seed["team_a"].id),
            "subject_name_snapshot": "Spoofed Name",
            "sanction_type": "tournament_ban",
            "public_reason": "Confirmed roster violation",
        },
    )
    assert sanction.status_code == 201
    assert sanction.json()["subject_name_snapshot"] == seed["team_a"].name

    tournament = _create_open_tournament(client, seed, slug="sanction-check-cup")
    blocked = client.post(
        f"/api/v1/tournaments/{tournament['id']}/registrations",
        headers=auth(seed["manager_a"]),
        json={"team_id": str(seed["team_a"].id), "roster_user_ids": [str(seed["player"].id)]},
    )
    assert blocked.status_code == 403

    forbidden = client.post(
        f"/api/v1/governance/blacklist/{sanction.json()['id']}/appeals",
        headers=auth(seed["outsider"]),
        json={"statement": "I am not authorized to appeal for this team."},
    )
    assert forbidden.status_code == 403
    appeal = client.post(
        f"/api/v1/governance/blacklist/{sanction.json()['id']}/appeals",
        headers=auth(seed["manager_a"]),
        json={"statement": "We corrected the roster violation and request review."},
    )
    assert appeal.status_code == 201
    decided = client.patch(
        f"/api/v1/governance/blacklist-appeals/{appeal.json()['id']}",
        headers=auth(seed["admin"]),
        json={"status": "resolved", "decision": "Corrective action verified.", "revoke_sanction": True},
    )
    assert decided.status_code == 200
    assert client.get("/api/v1/governance/blacklist").json() == []


def test_map_guides_enforce_public_curation_and_private_team_access(client, seed):
    public = client.post(
        "/api/v1/map-guides",
        headers=auth(seed["admin"]),
        json={
            "map_name": "Raid",
            "mode": "MP",
            "game_mode": "Hardpoint",
            "slot_number": 1,
            "custom_title": "CRA Raid Rotation Guide",
            "pdf_url": "https://cdn.example.com/raid.pdf",
            "is_curated": True,
        },
    )
    assert public.status_code == 201
    private = client.post(
        "/api/v1/map-guides",
        headers=auth(seed["manager_a"]),
        json={
            "team_id": str(seed["team_a"].id),
            "map_name": "Raid",
            "mode": "MP",
            "slot_number": 1,
            "custom_title": "NIM Breakoffs",
            "youtube_url": "https://youtu.be/example",
        },
    )
    assert private.status_code == 201
    assert client.get(f"/api/v1/map-guides/teams/{seed['team_a'].id}", headers=auth(seed["outsider"])).status_code == 403
    assert client.get(f"/api/v1/map-guides/teams/{seed['team_a'].id}", headers=auth(seed["player"])).status_code == 200
    promoted = client.put(
        f"/api/v1/map-guides/{private.json()['id']}",
        headers=auth(seed["manager_a"]),
        json={**private.json(), "is_curated": True},
    )
    assert promoted.status_code == 400
    curated = client.get("/api/v1/map-guides?map_name=Raid&mode=MP").json()
    assert [row["id"] for row in curated] == [public.json()["id"]]


def test_rich_org_permissions_achievement_verification_and_reputation(client, db, seed):
    organization = client.post(
        "/api/v1/orgs",
        headers=auth(seed["manager_a"]),
        json={"name": "NIM Group", "slug": "nim-group", "country_code": "NG", "founded_year": 2024},
    )
    assert organization.status_code == 201
    org_id = organization.json()["id"]
    staff = client.post(
        f"/api/v1/orgs/{org_id}/staff",
        headers=auth(seed["manager_a"]),
        json={"user_id": str(seed["outsider"].id), "role": "coach", "permissions": ["roster.manage"]},
    )
    assert staff.status_code == 201
    team = client.post(
        "/api/v1/teams",
        headers=auth(seed["outsider"]),
        json={
            "name": "NIM Academy",
            "region_id": str(seed["region"].id),
            "organization_id": org_id,
            "org_tier": "T3",
            "primary_mode": "MP",
        },
    )
    assert team.status_code == 201
    trophy = client.post(
        f"/api/v1/orgs/{org_id}/achievements",
        headers=auth(seed["manager_a"]),
        json={"team_id": team.json()["id"], "title": "Academy Cup", "category": "tournament"},
    )
    assert trophy.status_code == 201
    verified = client.patch(
        f"/api/v1/admin/achievements/{trophy.json()['id']}/verification",
        headers=auth(seed["admin"]),
        json={"verified": True, "note": "Result checked"},
    )
    assert verified.status_code == 200
    assert verified.json()["is_verified"] is True
    denied = client.post(
        "/api/v1/orgs/reputation-events",
        headers=auth(seed["outsider"]),
        json={"subject_type": "team", "subject_id": team.json()["id"], "delta": 5, "reason": "Great event"},
    )
    assert denied.status_code == 403
    changed = client.post(
        "/api/v1/orgs/reputation-events",
        headers=auth(seed["admin"]),
        json={"subject_type": "team", "subject_id": team.json()["id"], "delta": 5, "reason": "Verified fair play"},
    )
    assert changed.status_code == 201
    assert db.get(Achievement, uuid.UUID(trophy.json()["id"])).is_verified is True


def test_crowdfunding_and_merch_stock_lifecycle(client, db, seed):
    organization = client.post(
        "/api/v1/orgs",
        headers=auth(seed["manager_a"]),
        json={"name": "Rivals Commerce", "slug": "rivals-commerce", "country_code": "NG"},
    ).json()
    campaign = client.post(
        "/api/v1/commerce/campaigns",
        headers=auth(seed["manager_a"]),
        json={
            "organization_id": organization["id"],
            "title": "Travel to Africa Finals",
            "description": "Help the roster travel to the continental finals event.",
            "target_kobo": 100000,
        },
    )
    assert campaign.status_code == 201
    activated = client.patch(
        f"/api/v1/commerce/campaigns/{campaign.json()['id']}",
        headers=auth(seed["manager_a"]),
        json={"status": "active"},
    )
    assert activated.status_code == 200
    checkout = client.post(
        f"/api/v1/commerce/campaigns/{campaign.json()['id']}/contributions",
        headers=auth(seed["outsider"]),
        json={"amount_kobo": 10000, "email": "fan@example.com", "message": "Good luck!"},
    )
    assert checkout.status_code == 201
    transaction = db.get(PaymentTransaction, uuid.UUID(checkout.json()["transaction_id"]))
    mark_payment_success(
        db,
        reference=transaction.reference,
        provider_data={"amount": transaction.amount_kobo, "currency": "NGN", "id": 9001},
    )
    db.commit()
    assert db.get(CrowdfundingCampaign, uuid.UUID(campaign.json()["id"])).raised_kobo == 10000
    assert db.query(CampaignContribution).filter_by(confirmed_at=None).count() == 0

    product = client.post(
        "/api/v1/commerce/products",
        headers=auth(seed["manager_a"]),
        json={
            "organization_id": organization["id"],
            "name": "Rivals Jersey",
            "price_kobo": 10000,
            "stock_quantity": 2,
        },
    )
    assert product.status_code == 201
    order_checkout = client.post(
        "/api/v1/commerce/orders",
        headers=auth(seed["outsider"]),
        json={
            "organization_id": organization["id"],
            "email": "fan@example.com",
            "items": [{"product_id": product.json()["id"], "quantity": 2, "variant_key": "xl"}],
            "delivery_details": {"city": "Lagos", "address": "Pickup point"},
        },
    )
    assert order_checkout.status_code == 201
    db.expire_all()
    assert db.get(MerchProduct, uuid.UUID(product.json()["id"])).stock_quantity == 0
    mine = client.get("/api/v1/commerce/orders/me", headers=auth(seed["outsider"]))
    assert mine.status_code == 200 and len(mine.json()) == 1
    store_orders = client.get(
        f"/api/v1/commerce/orders?organization_id={organization['id']}",
        headers=auth(seed["manager_a"]),
    )
    assert store_orders.status_code == 200 and len(store_orders.json()) == 1
    cancelled = client.patch(
        f"/api/v1/commerce/orders/{mine.json()[0]['id']}",
        headers=auth(seed["manager_a"]),
        json={"status": "cancelled"},
    )
    assert cancelled.status_code == 200
    db.expire_all()
    assert db.get(MerchProduct, uuid.UUID(product.json()["id"])).stock_quantity == 2


def test_structured_vod_review_requires_roster_and_analyzes_without_raw_video(client, seed):
    week_start = date.today() - timedelta(days=date.today().weekday())
    invalid = client.post(
        "/api/v1/ai/vod-reviews",
        headers=auth(seed["manager_b"]),
        json={
            "player_id": str(seed["player"].id),
            "team_id": str(seed["team_b"].id),
            "mode": "MP",
            "match_date": str(date.today()),
            "overall_rating": 3,
            "strengths": ["comms"],
            "weaknesses": ["late_rotation"],
            "priority_focus": "rotation",
            "timestamp_notes": [{"timestamp": "04:12", "note": "Rotated after the hill changed."}],
            "week_start": str(week_start),
        },
    )
    assert invalid.status_code == 400
    created = client.post(
        "/api/v1/ai/vod-reviews",
        headers=auth(seed["manager_a"]),
        json={
            "player_id": str(seed["player"].id),
            "team_id": str(seed["team_a"].id),
            "mode": "MP",
            "match_date": str(date.today()),
            "overall_rating": 3,
            "strengths": ["comms"],
            "weaknesses": ["late_rotation"],
            "priority_focus": "rotation",
            "timestamp_notes": [{"timestamp": "04:12", "note": "Rotated after the hill changed."}],
            "week_start": str(week_start),
        },
    )
    assert created.status_code == 201
    analyzed = client.post(
        f"/api/v1/ai/vod-reviews/{created.json()['id']}/analyze",
        headers=auth(seed["manager_a"]),
    )
    assert analyzed.status_code == 200
    assert analyzed.json()["analysis_status"] == "ready"
    assert analyzed.json()["ai_findings"][0]["timestamp"] == "04:12"
