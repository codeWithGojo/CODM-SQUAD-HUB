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
    token = signed_up.json()["access_token"]
    restored = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert restored.status_code == 200
    assert restored.json()["gamertag"] == "NewPlayer"


def test_existing_player_login_wrong_code_reuse_and_me(client, seed, monkeypatch):
    monkeypatch.setattr(settings, "expose_dev_otp", True)
    phone = seed["player"].phone
    requested = client.post("/api/v1/auth/request-otp", json={"phone": phone})
    code = requested.json()["dev_code"]
    wrong = "0" * len(code) if code != "0" * len(code) else "1" * len(code)
    assert client.post("/api/v1/auth/verify-otp", json={"phone": phone, "code": wrong}).status_code == 400
    verified = client.post("/api/v1/auth/verify-otp", json={"phone": phone, "code": code})
    assert verified.status_code == 200
    assert verified.json()["is_new_user"] is False
    header = {"Authorization": f"Bearer {verified.json()['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=header).json()["id"] == str(seed["player"].id)
    assert client.post("/api/v1/auth/verify-otp", json={"phone": phone, "code": code}).status_code == 400
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_minor_signup_requires_distinct_guardian_contact_and_consent(client, db, seed, monkeypatch):
    monkeypatch.setattr(settings, "expose_dev_otp", True)
    phone = "+2348222222222"
    code = client.post("/api/v1/auth/request-otp", json={"phone": phone}).json()["dev_code"]
    token = client.post("/api/v1/auth/verify-otp", json={"phone": phone, "code": code}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    payload = {"phone": phone, "gamertag": "JuniorPlayer", "region_id": str(seed["region"].id),
               "is_adult": False, "parental_consent_confirmed": True}
    for guardian in [None, "bad", phone]:
        assert client.post("/api/v1/auth/complete-signup", headers=headers,
                           json={**payload, "guardian_phone": guardian}).status_code == 422
    guardian = "+2348333333333"
    assert client.post("/api/v1/auth/complete-signup", headers=headers,
                       json={**payload, "guardian_phone": guardian, "parental_consent_confirmed": False}).status_code == 422
    created = client.post("/api/v1/auth/complete-signup", headers=headers, json={**payload, "guardian_phone": guardian})
    assert created.status_code == 201
    assert db.query(User).filter_by(phone=phone).one().guardian_phone == guardian
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {created.json()['access_token']}"})
    assert me.status_code == 200
    assert "guardian_phone" not in me.json()


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
