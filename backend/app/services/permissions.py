from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import TeamRole
from app.models.organization_extra import OrganizationStaffMember
from app.models.team import Organization, Team, TeamMember
from app.models.user import User


def get_team_or_404(db: Session, team_id: uuid.UUID) -> Team:
    team = db.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    return team


def require_team_manager(db: Session, team_id: uuid.UUID, user: User) -> Team:
    team = get_team_or_404(db, team_id)
    if user.is_platform_admin or team.manager_id == user.id:
        return team
    membership = (
        db.query(TeamMember.id)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user.id,
            TeamMember.is_active.is_(True),
            TeamMember.role == TeamRole.MANAGER,
        )
        .first()
    )
    if not membership:
        if team.organization_id:
            org = db.get(Organization, team.organization_id)
            staff = (
                db.query(OrganizationStaffMember)
                .filter(
                    OrganizationStaffMember.organization_id == team.organization_id,
                    OrganizationStaffMember.user_id == user.id,
                    OrganizationStaffMember.is_active.is_(True),
                )
                .first()
            )
            if (org and org.owner_id == user.id) or (staff and ("roster.manage" in staff.permissions or "*" in staff.permissions)):
                return team
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team manager access required.")
    return team


def require_org_permission(
    db: Session,
    organization_id: uuid.UUID,
    user: User,
    permission: str,
) -> Organization:
    org = db.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    if user.is_platform_admin or org.owner_id == user.id:
        return org
    staff = (
        db.query(OrganizationStaffMember)
        .filter(
            OrganizationStaffMember.organization_id == organization_id,
            OrganizationStaffMember.user_id == user.id,
            OrganizationStaffMember.is_active.is_(True),
        )
        .first()
    )
    if not staff or (permission not in staff.permissions and "*" not in staff.permissions):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Organization permission '{permission}' required.")
    return org


def require_chat_participant(db: Session, thread_id: uuid.UUID, user_id: uuid.UUID):
    from app.models.communication import ChatParticipant

    row = (
        db.query(ChatParticipant)
        .filter(
            ChatParticipant.thread_id == thread_id,
            ChatParticipant.user_id == user_id,
            ChatParticipant.is_active.is_(True),
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a participant in this chat.")
    return row
