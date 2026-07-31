import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.team import Organization, Team, TeamMember
from app.models.enums import TeamRole
from app.schemas.organization import (
    CreateOrganizationIn,
    OrganizationOut,
    CreateTeamIn,
    TeamOut,
    InviteMemberIn,
    TeamMemberOut,
    PromotePlayerIn,
)
from app.services.team_moves import move_player_to_team

router = APIRouter(prefix="/orgs", tags=["organizations"])
teams_router = APIRouter(prefix="/teams", tags=["teams"])


# ---------- Organizations ----------

@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: CreateOrganizationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Organization).filter(Organization.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="An organization with that name already exists.")

    org = Organization(name=payload.name, logo_url=payload.logo_url, owner_id=current_user.id)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("/{org_id}", response_model=OrganizationOut)
def get_organization(org_id: uuid.UUID, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return org


@router.get("/{org_id}/teams", response_model=list[TeamOut])
def list_organization_teams(org_id: uuid.UUID, db: Session = Depends(get_db)):
    """All rosters under an org — e.g. N¡M First, Second, Academy, Development."""
    return db.query(Team).filter(Team.organization_id == org_id).all()


# ---------- Teams ----------

@teams_router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: CreateTeamIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a team. organization_id is optional — a standalone squad with
    no org is a fully valid setup (locked decision). If organization_id
    IS set, only that org's owner can add a roster under it.
    """
    if payload.organization_id:
        org = db.query(Organization).filter(Organization.id == payload.organization_id).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found.")
        if org.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the org owner can add a team under it.")
        if payload.org_tier is None:
            raise HTTPException(status_code=400, detail="org_tier is required when creating a team under an organization.")

    team = Team(
        name=payload.name,
        region_id=payload.region_id,
        organization_id=payload.organization_id,
        org_tier=payload.org_tier,
        manager_id=current_user.id,  # creator becomes manager by default
        logo_url=payload.logo_url,
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    # Creator is automatically the manager and a member of their own team.
    db.add(TeamMember(team_id=team.id, user_id=current_user.id, role=TeamRole.MANAGER))
    db.commit()

    return team


@teams_router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: uuid.UUID, db: Session = Depends(get_db)):
    return _get_team_or_404(db, team_id)


@teams_router.get("/{team_id}/members", response_model=list[TeamMemberOut])
def list_team_members(team_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.is_active == True)  # noqa: E712
        .all()
    )


@teams_router.post("/{team_id}/members", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
def invite_member(
    team_id: uuid.UUID,
    payload: InviteMemberIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manager-only: add a player to the roster."""
    team = _get_team_or_404(db, team_id)
    _require_manager(team, current_user)

    already_on_team = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == payload.user_id, TeamMember.is_active == True)  # noqa: E712
        .first()
    )
    if already_on_team:
        raise HTTPException(status_code=400, detail="That user is already on this team's roster.")

    member = TeamMember(team_id=team_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
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
    """Manager-only: remove a player from the roster (becomes a free agent)."""
    team = _get_team_or_404(db, team_id)
    _require_manager(team, current_user)

    membership = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id, TeamMember.is_active == True)  # noqa: E712
        .first()
    )
    if not membership:
        raise HTTPException(status_code=404, detail="That user is not an active member of this team.")

    membership.is_active = False
    membership.left_at = datetime.utcnow()
    db.commit()
    return None


@teams_router.post("/{team_id}/members/{user_id}/promote", response_model=TeamMemberOut)
def promote_player(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: PromotePlayerIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Move a player between rosters within the same org (e.g. Academy ->
    First Team). Requires being the manager of BOTH the origin and
    destination teams (typically the org owner, since orgs usually
    share management). Auto-logs a PlayerTimelineEvent; personal stats
    are untouched by design (see app/services/team_moves.py).
    """
    from_team = _get_team_or_404(db, team_id)
    to_team = _get_team_or_404(db, payload.to_team_id)
    _require_manager(from_team, current_user)
    _require_manager(to_team, current_user)

    org_tier_label = to_team.org_tier.value if to_team.org_tier else to_team.name
    description = f"Moved from {from_team.name} to {to_team.name} ({org_tier_label})"

    return move_player_to_team(
        db,
        user_id=user_id,
        to_team_id=payload.to_team_id,
        new_role=payload.new_role,
        event_type="promotion",
        description=description,
    )


# ---------- shared helpers ----------

def _get_team_or_404(db: Session, team_id: uuid.UUID) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found.")
    return team


def _require_manager(team: Team, current_user: User) -> None:
    if team.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only this team's manager can do that.")
