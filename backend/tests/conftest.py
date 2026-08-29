from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import models  # noqa: F401
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import create_access_token
from app.main import app
from app.models.enums import Mode, TeamRole, TournamentOrganizerStatus
from app.models.organizer import TournamentOrganizerApplication
from app.models.team import Team, TeamMember
from app.models.user import Region, User


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def seed(db):
    region = db.query(Region).filter(Region.code == "NG").first()
    if not region:
        region = Region(name="Nigeria", code="NG", zone="West Africa")
        db.add(region)
        db.flush()
    admin = User(phone="+2348000000001", gamertag="CRAAdmin", region_id=region.id, is_platform_admin=True)
    organizer = User(phone="+2348000000002", gamertag="EventHost", region_id=region.id)
    manager_a = User(phone="+2348000000003", gamertag="ManagerA", region_id=region.id)
    manager_b = User(phone="+2348000000004", gamertag="ManagerB", region_id=region.id)
    player = User(phone="+2348000000005", gamertag="StarPlayer", region_id=region.id, preferred_mode=Mode.MP)
    outsider = User(phone="+2348000000006", gamertag="Outsider", region_id=region.id)
    db.add_all([admin, organizer, manager_a, manager_b, player, outsider])
    db.flush()
    team_a = Team(name="NIM Esports", region_id=region.id, manager_id=manager_a.id, primary_mode="MP")
    team_b = Team(name="Raven Esports", region_id=region.id, manager_id=manager_b.id, primary_mode="MP")
    db.add_all([team_a, team_b])
    db.flush()
    db.add_all(
        [
            TeamMember(team_id=team_a.id, user_id=manager_a.id, role=TeamRole.MANAGER),
            TeamMember(team_id=team_b.id, user_id=manager_b.id, role=TeamRole.MANAGER),
            TeamMember(team_id=team_a.id, user_id=player.id, role=TeamRole.PLAYER),
            TournamentOrganizerApplication(
                user_id=organizer.id,
                reason_for_applying="I run verified community events.",
                status=TournamentOrganizerStatus.APPROVED,
                reviewed_by=admin.id,
            ),
        ]
    )
    db.commit()
    return {
        "region": region,
        "admin": admin,
        "organizer": organizer,
        "manager_a": manager_a,
        "manager_b": manager_b,
        "player": player,
        "outsider": outsider,
        "team_a": team_a,
        "team_b": team_b,
    }


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}
