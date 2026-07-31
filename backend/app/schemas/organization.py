import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import OrgTier, TeamRole


# ---------- Organizations ----------

class CreateOrganizationIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    logo_url: str | None = None


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    logo_url: str | None
    owner_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Teams ----------

class CreateTeamIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    region_id: uuid.UUID
    # Optional — a team does NOT need to belong to an org (locked decision).
    organization_id: uuid.UUID | None = None
    org_tier: OrgTier | None = None
    logo_url: str | None = None


class TeamOut(BaseModel):
    id: uuid.UUID
    name: str
    region_id: uuid.UUID
    organization_id: uuid.UUID | None
    org_tier: OrgTier | None
    competitive_tier_mp: int
    competitive_tier_br: int
    manager_id: uuid.UUID | None
    logo_url: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Team Membership ----------

class InviteMemberIn(BaseModel):
    user_id: uuid.UUID
    role: TeamRole = TeamRole.PLAYER


class TeamMemberOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    user_id: uuid.UUID
    role: TeamRole
    is_active: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


class PromotePlayerIn(BaseModel):
    """Move a player from one team to another WITHIN the same org (e.g. Academy -> First Team)."""
    to_team_id: uuid.UUID
    new_role: TeamRole = TeamRole.PLAYER
