from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import uuid

from app.models.ai_review import AIWeeklyReview, TrainingAssignment
from app.models.commerce import TeamSubscription
from app.models.communication import Notification
from app.models.enums import BillingCycle, PaymentPurpose, PaymentStatus, PlayerContractStatus, SubscriptionTier
from app.models.team import TeamMember
from app.models.transfer import Contract, TransferOffer
from app.services.payments import initialize_payment, mark_payment_success, plan_price
from tests.conftest import auth


def test_transfer_requires_club_and_player_consent_then_moves_contract(client, db, seed):
    contract = Contract(
        player_id=seed["player"].id,
        team_id=seed["team_a"].id,
        status=PlayerContractStatus.UNDER_CONTRACT,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=365),
    )
    db.add(contract)
    db.commit()
    offer = client.post(
        "/api/v1/transfers/offers",
        headers=auth(seed["manager_b"]),
        json={
            "player_id": str(seed["player"].id),
            "to_team_id": str(seed["team_b"].id),
            "offer_type": "permanent",
            "transfer_fee_naira": 250000,
            "proposed_salary_naira": 50000,
            "proposed_contract_length_months": 12,
        },
    )
    assert offer.status_code == 201
    offer_id = uuid.UUID(offer.json()["id"])
    assert offer.json()["status"] == "pending_club_review"
    approved = client.post(
        f"/api/v1/transfers/offers/{offer_id}/club-decision",
        headers=auth(seed["manager_a"]),
        json={"decision": "approve"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "pending_player_review"
    accepted = client.post(
        f"/api/v1/transfers/offers/{offer_id}/player-decision",
        headers=auth(seed["player"]),
        json={"accept": True},
    )
    assert accepted.status_code == 200
    completed = client.post(f"/api/v1/transfers/offers/{offer_id}/complete", headers=auth(seed["manager_b"]))
    assert completed.status_code == 200
    assert completed.json()["team_id"] == str(seed["team_b"].id)
    db.expire_all()
    assert db.get(TransferOffer, offer_id).status.value == "completed"
    memberships = db.query(TeamMember).filter_by(user_id=seed["player"].id, is_active=True).all()
    assert [row.team_id for row in memberships] == [seed["team_b"].id]


def test_weekly_ai_review_uses_rules_fallback_and_assigns_drills(client, db, seed):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    played_at = datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=12)
    logged = client.post(
        "/api/v1/performance/matches",
        headers=auth(seed["player"]),
        json={
            "team_id": str(seed["team_a"].id),
            "mode": "MP",
            "game_mode": "Hardpoint",
            "map_name": "Raid",
            "result": "win",
            "kills": 20,
            "deaths": 10,
            "assists": 8,
            "damage": 4500,
            "objective_score": 120,
            "tags": ["late_rotation", "late_rotation"],
            "played_at": played_at.isoformat(),
        },
    )
    assert logged.status_code == 201
    review = client.post(
        "/api/v1/ai/weekly-reviews/run",
        headers=auth(seed["player"]),
        json={"week_start": str(week_start)},
    )
    assert review.status_code == 200
    assert review.json()["status"] == "ready"
    assert review.json()["generator"] == "rules"
    assert db.query(TrainingAssignment).count() >= 1


def test_payment_success_is_idempotent_and_grants_team_plan(db, seed):
    amount = plan_price(SubscriptionTier.PRO, BillingCycle.MONTHLY)
    transaction, configured = initialize_payment(
        db,
        user_id=seed["manager_a"].id,
        email="manager@example.com",
        purpose=PaymentPurpose.SUBSCRIPTION,
        amount_kobo=amount,
        target_type="team",
        target_id=seed["team_a"].id,
        metadata={"tier": "pro", "billing_cycle": "monthly"},
    )
    db.commit()
    assert configured is False
    provider = {"amount": amount, "currency": "NGN", "id": 12345}
    mark_payment_success(db, reference=transaction.reference, provider_data=provider)
    mark_payment_success(db, reference=transaction.reference, provider_data=provider)
    db.commit()
    assert transaction.status == PaymentStatus.SUCCESS
    subscription = db.query(TeamSubscription).filter_by(team_id=seed["team_a"].id).one()
    assert subscription.tier == SubscriptionTier.PRO


def test_chat_permissions_and_notification(client, db, seed):
    thread = client.post(
        "/api/v1/chat/threads",
        headers=auth(seed["manager_a"]),
        json={"thread_type": "direct", "participant_ids": [str(seed["manager_b"].id)]},
    )
    assert thread.status_code == 201
    thread_id = thread.json()["id"]
    sent = client.post(
        f"/api/v1/chat/threads/{thread_id}/messages",
        headers=auth(seed["manager_a"]),
        json={"body": "Scrim at 8pm?"},
    )
    assert sent.status_code == 201
    forbidden = client.get(f"/api/v1/chat/threads/{thread_id}/messages", headers=auth(seed["outsider"]))
    assert forbidden.status_code == 403
    assert db.query(Notification).filter_by(user_id=seed["manager_b"].id).count() == 1


def test_websocket_auth_and_channel_authorization(client, seed):
    thread = client.post(
        "/api/v1/chat/threads",
        headers=auth(seed["manager_a"]),
        json={"thread_type": "direct", "participant_ids": [str(seed["manager_b"].id)]},
    ).json()
    token = auth(seed["manager_a"])["Authorization"].split(" ", 1)[1]
    with client.websocket_connect("/api/v1/ws") as socket:
        socket.send_json({"type": "auth", "token": token})
        assert socket.receive_json()["type"] == "auth.ok"
        socket.send_json({"type": "subscribe", "channel": f"chat:{thread['id']}"})
        assert socket.receive_json()["type"] == "subscribed"
        socket.send_json({"type": "subscribe", "channel": f"chat:{seed['outsider'].id}"})
        assert socket.receive_json()["code"] == "channel_forbidden"
