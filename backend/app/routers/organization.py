from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_platform_admin
from app.core.time import utcnow
from app.models.enums import AuditAction, CareerStatus, OrgStaffRole, PlayerContractStatus, TeamRole
from app.models.organization_extra import (
    Achievement,
    AuditLog,
    HallOfFameEntry,
    OrganizationStaffMember,
    PlayerRetirement,
    ReputationEvent,
)
from app.models.team import Organization, PlayerTimelineEvent, Team, TeamMember
from app.models.transfer import Contract
from app.models.user import Region, User
from app.schemas.organization import (
    AchievementIn,
    CreateOrganizationIn,
    CreateTeamIn,
    HallOfFameIn,
    InviteMemberIn,
    OrganizationOut,
    OrganizationStaffIn,
    OrganizationStaffOut,
    PromotePlayerIn,
    ReputationEventIn,
    RetirementIn,
    TeamMemberOut,
    TeamOut,
)
from app.services.permissions import get_team_or_404, require_org_permission, require_team_manager
from app.services.team_moves import move_player_to_team

router = APIRouter(prefix="/orgs", tags=["organizations"])
teams_router = APIRouter(prefix="/teams", tags=["teams"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: CreateOrganizationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    slug = payload.slug or _slugify(payload.name)
    if db.query(Organization.id).filter((Organization.name == payload.name) | (Organization.slug == slug)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization name or slug already exists.")
    org = Organization(owner_id=current_user.id, slug=slug, **payload.model_dump(exclude={"slug"}))
    db.add(org)
    db.flush()
    db.add(
        OrganizationStaffMember(
            organization_id=org.id,
            user_id=current_user.id,
            role=OrgStaffRole.OWNER,
            permissions=["*"],
            invited_by=current_user.id,
        )
    )
    db.add(AuditLog(actor_user_id=current_user.id, action=AuditAction.CREATE, target_type="organization", target_id=org.id, summary=f"Created {org.name}"))
    db.commit()
    db.refresh(org)
    return org


@router.get("/{org_id}", response_model=OrganizationOut)
def get_organization(org_id: uuid.UUID, db: Session = Depends(get_db)):
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return org


@router.get("/{org_id}/teams", response_model=list[TeamOut])
def list_organization_teams(org_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(Team).filter(Team.organization_id == org_id, Team.is_active.is_(True)).all()


@router.get("/{org_id}/staff", response_model=list[OrganizationStaffOut])
def list_staff(org_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(OrganizationStaffMember).filter(OrganizationStaffMember.organization_id == org_id, OrganizationStaffMember.is_active.is_(True)).all()


@router.post("/{org_id}/staff", response_model=OrganizationStaffOut, status_code=status.HTTP_201_CREATED)
def add_staff(
    org_id: uuid.UUID,
    payload: OrganizationStaffIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_permission(db, org_id, current_user, "staff.manage")
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    org = db.get(Organization, org_id)
    if payload.role == OrgStaffRole.OWNER and (not org or payload.user_id != org.owner_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ownership cannot be assigned as a staff role.")
    existing = db.query(OrganizationStaffMember).filter_by(organization_id=org_id, user_id=payload.user_id).first()
    if existing:
        existing.role = payload.role
        existing.custom_title = payload.custom_title
        existing.permissions = payload.permissions
        existing.is_active = True
        row = existing
    else:
        row = OrganizationStaffMember(
            organization_id=org_id,
            invited_by=current_user.id,
            **payload.model_dump(),
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{org_id}/staff/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_staff(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = require_org_permission(db, org_id, current_user, "staff.manage")
    if org.owner_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The organization owner cannot be removed.")
    row = db.query(OrganizationStaffMember).filter_by(organization_id=org_id, user_id=user_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found.")
    row.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{org_id}/achievements", status_code=status.HTTP_201_CREATED)
def add_achievement(
    org_id: uuid.UUID,
    payload: AchievementIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_permission(db, org_id, current_user, "history.manage")
    if payload.user_id and not db.get(User, payload.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achievement player not found.")
    if payload.team_id:
        team = db.get(Team, payload.team_id)
        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Achievement team not found.")
        if team.organization_id != org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Achievement team does not belong to this organization.")
    row = Achievement(organization_id=org_id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{org_id}/achievements")
def list_achievements(org_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(Achievement).filter(Achievement.organization_id == org_id).order_by(Achievement.awarded_at.desc()).all()


@router.post("/{org_id}/hall-of-fame", status_code=status.HTTP_201_CREATED)
def add_hall_of_fame_entry(
    org_id: uuid.UUID,
    payload: HallOfFameIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_org_permission(db, org_id, current_user, "history.manage")
    if payload.entity_type == "organization" and payload.entity_id != org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization Hall of Fame entries must target this organization.")
    if payload.entity_type == "team":
        team = db.get(Team, payload.entity_id)
        if not team or team.organization_id != org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hall of Fame team must belong to this organization.")
    if payload.entity_type == "player" and not db.get(User, payload.entity_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hall of Fame player not found.")
    row = HallOfFameEntry(scope="organization", organization_id=org_id, inducted_by=current_user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{org_id}/hall-of-fame")
def list_hall_of_fame(org_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(HallOfFameEntry).filter(HallOfFameEntry.organization_id == org_id).order_by(HallOfFameEntry.inducted_at.desc()).all()


@teams_router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: CreateTeamIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not db.get(Region, payload.region_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown region_id.")
    if payload.organization_id:
        require_org_permission(db, payload.organization_id, current_user, "roster.manage")
    team = Team(manager_id=current_user.id, **payload.model_dump())
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=current_user.id, role=TeamRole.MANAGER))
    db.commit()
    db.refresh(team)
    return team


@teams_router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: uuid.UUID, db: Session = Depends(get_db)):
    return get_team_or_404(db, team_id)


@teams_router.get("/{team_id}/members", response_model=list[TeamMemberOut])
def list_team_members(team_id: uuid.UUID, db: Session = Depends(get_db)):
    get_team_or_404(db, team_id)
    return db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.is_active.is_(True)).all()


@teams_router.post("/{team_id}/members", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
def invite_member(
    team_id: uuid.UUID,
    payload: InviteMemberIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, team_id, current_user)
    if not db.get(User, payload.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    active = db.query(TeamMember).filter(TeamMember.user_id == payload.user_id, TeamMember.is_active.is_(True)).first()
    if active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Player already has an active team; use promotion or transfer.")
    member = TeamMember(team_id=team_id, **payload.model_dump())
    db.add(member)
    db.add(PlayerTimelineEvent(user_id=payload.user_id, event_type="signed", description="Joined team", to_team_id=team_id))
    db.commit()
    db.refresh(member)
    return member


@teams_router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_team_manager(db, team_id, current_user)
    row = db.query(TeamMember).filter_by(team_id=team_id, user_id=user_id, is_active=True).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active member not found.")
    team = db.get(Team, team_id)
    if team and team.manager_id == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assign a new team manager before removing this manager.")
    row.is_active = False
    row.left_at = utcnow()
    contract = db.query(Contract).filter_by(player_id=user_id, team_id=team_id, is_active=True).first()
    if contract:
        contract.is_active = False
        contract.status = PlayerContractStatus.TERMINATED
    db.add(PlayerTimelineEvent(user_id=user_id, event_type="released", description="Released as a free agent", from_team_id=team_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@teams_router.post("/{team_id}/members/{user_id}/move", response_model=TeamMemberOut)
def move_player(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: PromotePlayerIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    origin = require_team_manager(db, team_id, current_user)
    destination = require_team_manager(db, payload.to_team_id, current_user)
    if not origin.organization_id or origin.organization_id != destination.organization_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Internal moves require teams in the same organization.")
    active_origin = (
        db.query(TeamMember.id)
        .filter(
            TeamMember.team_id == origin.id,
            TeamMember.user_id == user_id,
            TeamMember.is_active.is_(True),
            TeamMember.role.in_([TeamRole.PLAYER, TeamRole.SUBSTITUTE]),
        )
        .first()
    )
    if not active_origin:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Player is not active on the origin roster.")
    description = f"{payload.event_type.title()} from {origin.name} to {destination.name}"
    return move_player_to_team(
        db,
        user_id=user_id,
        to_team_id=destination.id,
        new_role=payload.new_role,
        event_type=payload.event_type,
        description=description,
    )


@teams_router.post("/{team_id}/members/{user_id}/retire", status_code=status.HTTP_201_CREATED)
def retire_player(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: RetirementIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.id != user_id and not current_user.is_platform_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the player can retire their career.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if db.query(PlayerRetirement.id).filter(PlayerRetirement.user_id == user_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Retirement already recorded.")
    if not db.get(Team, team_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    if not db.query(TeamMember.id).filter_by(team_id=team_id, user_id=user_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The selected last team is not in this player's roster history.")
    user.career_status = CareerStatus.RETIRED
    active_rows = db.query(TeamMember).filter(
        TeamMember.user_id == user_id,
        TeamMember.is_active.is_(True),
        TeamMember.role.in_([TeamRole.PLAYER, TeamRole.SUBSTITUTE]),
    ).all()
    for active in active_rows:
        active.is_active = False
        active.left_at = utcnow()
    for contract in db.query(Contract).filter_by(player_id=user_id, is_active=True).all():
        contract.is_active = False
        contract.status = PlayerContractStatus.TERMINATED
    row = PlayerRetirement(user_id=user_id, last_team_id=team_id, recorded_by=current_user.id, **payload.model_dump())
    db.add(row)
    db.add(PlayerTimelineEvent(user_id=user_id, event_type="retirement", description="Retired from competitive play", from_team_id=team_id))
    db.commit()
    db.refresh(row)
    return row


@router.post("/reputation-events", status_code=status.HTTP_201_CREATED)
def create_reputation_event(
    payload: ReputationEventIn,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    model = {"player": User, "team": Team, "organization": Organization}[payload.subject_type]
    subject = db.get(model, payload.subject_id)
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reputation subject not found.")
    subject.reputation_score = max(0, min(100, subject.reputation_score + payload.delta))
    row = ReputationEvent(created_by=current_user.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
