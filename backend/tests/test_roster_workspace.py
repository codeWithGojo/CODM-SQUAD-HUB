from datetime import date, timedelta
import uuid

import pytest

from app.core.time import utcnow
from app.models.enums import Mode, RegistrationStatus, TournamentStatus, TournamentFormat
from app.models.team import PlayerTimelineEvent, TeamMember
from app.models.tournament import Tournament, TournamentRegistration
from app.models.transfer import Contract
from tests.conftest import auth


def setup_org(client, seed):
    header = auth(seed['manager_a'])
    response = client.post('/api/v1/orgs', headers=header, json={'name': 'NIM Pilot'})
    assert response.status_code == 201, response.text
    org = response.json()
    teams = []
    for tier in ['T1', 'T2', 'T3', 'T4']:
        response = client.post('/api/v1/teams', headers=header, json={
            'name': f'NIM {tier}', 'organization_id': org['id'], 'org_tier': tier,
            'region_id': str(seed['region'].id), 'primary_mode': 'MP',
        })
        assert response.status_code == 201, response.text
        teams.append(response.json())
    return header, org, teams


def test_owner_creates_four_tiers_and_reloads_only_accessible_workspaces(client, seed):
    header, org, teams = setup_org(client, seed)
    mine = client.get('/api/v1/orgs/mine', headers=header).json()
    assert mine[0]['id'] == org['id'] and mine[0]['can_manage_roster']
    saved = client.get('/api/v1/teams/mine', headers=header).json()
    assert {row['org_tier'] for row in saved if row['organization_id'] == org['id']} == {'T1', 'T2', 'T3', 'T4'}
    assert client.get('/api/v1/orgs/mine', headers=auth(seed['outsider'])).json() == []
    assert client.get('/api/v1/teams/mine', headers=auth(seed['outsider'])).json() == []
    denied = client.post('/api/v1/teams', headers=auth(seed['outsider']), json={
        'name': 'Forged', 'organization_id': org['id'], 'org_tier': 'T1', 'region_id': str(seed['region'].id)})
    assert denied.status_code == 403
    duplicate = client.post('/api/v1/teams', headers=header, json={
        'name': 'NIM T1', 'organization_id': org['id'], 'org_tier': 'T1', 'region_id': str(seed['region'].id)})
    assert duplicate.status_code == 409


def test_player_lookup_add_move_release_and_personal_timeline(client, seed, db):
    header, org, teams = setup_org(client, seed)
    player = seed['outsider']
    found = client.get(f'/api/v1/teams/players/by-shid/{player.shid.lower()}', headers=header).json()
    assert found['id'] == str(player.id)
    assert 'phone' not in found and 'guardian_phone' not in found and 'email' not in found
    source, destination = teams[2]['id'], teams[0]['id']
    added = client.post(f'/api/v1/teams/{source}/members', headers=header,
                        json={'user_id': found['id'], 'role': 'player', 'in_game_role': 'OBJ'})
    assert added.status_code == 201
    rows = client.get(f'/api/v1/teams/{source}/members').json()
    assert any(row['shid'] == player.shid and row['gamertag'] == player.gamertag for row in rows)
    assert client.post(f'/api/v1/teams/{destination}/members', headers=header,
                       json={'user_id': found['id']}).status_code == 409
    readonly = client.get('/api/v1/teams/mine', headers=auth(player)).json()
    assert all(not row['can_manage_roster'] for row in readonly)
    assert client.post(f'/api/v1/teams/{source}/members/{player.id}/move', headers=auth(player),
                       json={'to_team_id': destination}).status_code == 403
    moved = client.post(f'/api/v1/teams/{source}/members/{player.id}/move', headers=header,
                        json={'to_team_id': destination, 'event_type': 'demotion'})
    assert moved.status_code == 200, moved.text
    assert moved.json()['in_game_role'] == 'OBJ'
    timeline = client.get('/api/v1/teams/timeline/me', headers=auth(player)).json()
    assert timeline[0]['event_type'] == 'promotion'  # Derived from structural tiers on server.
    assert client.post(f'/api/v1/teams/{source}/members/{player.id}/move', headers=header,
                       json={'to_team_id': destination}).status_code == 409
    assert client.delete(f'/api/v1/teams/{destination}/members/{player.id}', headers=header).status_code == 204
    assert client.get('/api/v1/teams/timeline/me', headers=auth(player)).json()[0]['event_type'] == 'released'
    assert db.query(PlayerTimelineEvent).filter_by(user_id=player.id).count() == 3


@pytest.mark.parametrize('status,dated', [(TournamentStatus.LIVE, False), (TournamentStatus.ROSTER_LOCKED, False), (TournamentStatus.REGISTRATION, True)])
def test_active_event_roster_locks_block_add_remove_and_move(client, seed, db, status, dated):
    header, _, teams = setup_org(client, seed)
    source, dest = teams[0]['id'], teams[1]['id']
    player = seed['outsider']
    assert client.post(f'/api/v1/teams/{source}/members', headers=header, json={'user_id': str(player.id)}).status_code == 201
    event = Tournament(organizer_id=seed['organizer'].id, name='Pilot Lock', slug='pilot-lock', mode=Mode.MP,
                       starts_at=utcnow(), format=TournamentFormat.ROUND_ROBIN, status=status, roster_lock_at=utcnow() - timedelta(hours=1) if dated else None)
    db.add(event); db.flush()
    registration = TournamentRegistration(tournament_id=event.id, team_id=uuid.UUID(source), submitted_by=seed['manager_a'].id,
                                         status=RegistrationStatus.APPROVED, roster_user_ids=[str(player.id)])
    db.add(registration); db.commit()
    assert client.delete(f'/api/v1/teams/{source}/members/{player.id}', headers=header).status_code == 409
    assert client.post(f'/api/v1/teams/{source}/members/{player.id}/move', headers=header, json={'to_team_id': dest}).status_code == 409
    assert client.post(f'/api/v1/teams/{source}/members', headers=header, json={'user_id': str(seed['manager_b'].id)}).status_code == 409
    db.refresh(event); event.status = TournamentStatus.COMPLETED; db.commit()
    assert client.delete(f'/api/v1/teams/{source}/members/{player.id}', headers=header).status_code == 204


def test_roster_controls_cannot_assign_manager_or_release_active_contract(client, seed, db):
    header = auth(seed['manager_a'])
    team = seed['team_a']
    assert client.post(f'/api/v1/teams/{team.id}/members', headers=header,
                       json={'user_id': str(seed['outsider'].id), 'role': 'manager'}).status_code == 400
    contract = Contract(player_id=seed['player'].id, team_id=team.id,
                        start_date=date.today(), end_date=date.today() + timedelta(days=30))
    db.add(contract); db.commit()
    assert client.delete(f'/api/v1/teams/{team.id}/members/{seed["player"].id}', headers=header).status_code == 409
    db.refresh(contract)
    assert contract.is_active
    assert db.query(TeamMember).filter_by(team_id=team.id, user_id=seed['player'].id, is_active=True).count() == 1


def test_standalone_squad_does_not_need_org_tier(client, seed):
    result = client.post('/api/v1/teams', headers=auth(seed['outsider']), json={
        'name': 'Independent Squad', 'region_id': str(seed['region'].id), 'primary_mode': 'BR'})
    assert result.status_code == 201
    assert result.json()['org_tier'] is None and result.json()['organization_id'] is None
