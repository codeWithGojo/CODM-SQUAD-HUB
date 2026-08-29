from __future__ import annotations

from app.core.config import settings
from app.models.user import User
from tests.conftest import auth


def test_public_region_directory_is_seeded(client):
    response = client.get("/api/v1/regions")
    assert response.status_code == 200
    regions = response.json()
    assert len(regions) == 54
    assert any(row["code"] == "NG" and row["zone"] == "West Africa" for row in regions)


def test_phone_otp_signup_and_privacy_hashing(client, db, seed, monkeypatch):
    monkeypatch.setattr(settings, "expose_dev_otp", True)
    phone = "+2348111111111"
    requested = client.post(
        "/api/v1/auth/request-otp",
        json={"phone": phone},
        headers={"X-Device-Fingerprint": "pixel-9-local-id"},
    )
    assert requested.status_code == 202
    code = requested.json()["dev_code"]
    verified = client.post("/api/v1/auth/verify-otp", json={"phone": phone, "code": code})
    assert verified.status_code == 200
    signup_token = verified.json()["access_token"]
    signed_up = client.post(
        "/api/v1/auth/complete-signup",
        headers={"Authorization": f"Bearer {signup_token}", "X-Device-Fingerprint": "pixel-9-local-id"},
        json={
            "phone": phone,
            "gamertag": "NewPlayer",
            "region_id": str(seed["region"].id),
            "preferred_mode": "MP",
            "is_adult": True,
        },
    )
    assert signed_up.status_code == 201
    row = db.query(User).filter_by(phone=phone).one()
    assert row.device_fingerprint_hash
    assert row.device_fingerprint_hash != "pixel-9-local-id"


def test_tournament_organizer_role_is_enforced(client, seed):
    payload = {
        "name": "West Africa Open",
        "slug": "west-africa-open",
        "mode": "MP",
        "format": "single_elimination",
        "starts_at": "2026-10-01T18:00:00Z",
    }
    forbidden = client.post("/api/v1/tournaments", headers=auth(seed["outsider"]), json=payload)
    assert forbidden.status_code == 403
    allowed = client.post("/api/v1/tournaments", headers=auth(seed["organizer"]), json=payload)
    assert allowed.status_code == 201


def test_admin_dashboard_rejects_non_admin(client, seed):
    assert client.get("/api/v1/admin/dashboard", headers=auth(seed["manager_a"])).status_code == 403
    response = client.get("/api/v1/admin/dashboard", headers=auth(seed["admin"]))
    assert response.status_code == 200
    assert response.json()["users"] == 6
