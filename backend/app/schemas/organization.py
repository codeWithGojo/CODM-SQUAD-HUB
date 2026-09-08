from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import OrgStaffRole, OrgTier, TeamRole, VerificationStatus


class ORMModel(BaseModel):
    model_config = {"from_attributes": True}


class CreateOrganizationIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    slug: str | None = Field(default=None, min_length=2, max_length=120, pattern=r"^[a-z0-9-]+$")
    logo_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=1000)
    country_code: str | None = Field(default=None, max_length=10)
    founded_year: int | None = Field(default=None, ge=2000, le=2100)


class OrganizationOut(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    logo_url: str | None
    description: str | None
    country_code: str | None
    owner_id: uuid.UUID
    verification_status: VerificationStatus
    reputation_score: int
    founded_year: int | None
    is_active: bool
    created_at: datetime


class OrganizationStaffIn(BaseModel):
    user_id: uuid.UUID
    role: OrgStaffRole
    custom_title: str | None = Field(default=None, max_length=100)
    permissions: list[str] = Field(default_factory=list, max_length=30)


class OrganizationStaffOut(ORMModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: OrgStaffRole
    custom_title: str | None
    permissions: list[str]
    is_active: bool
    joined_at: datetime


class CreateTeamIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    region_id: uuid.UUID
    organization_id: uuid.UUID | None = None
    org_tier: OrgTier | None = None
    primary_mode: str | None = Field(default=None, pattern=r"^(MP|BR)$")
    logo_url: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def require_org_tier(self):
        if self.organization_id and self.org_tier is None:
            raise ValueError("org_tier is required for an organization roster")
        if not self.organization_id and self.org_tier is not None:
            raise ValueError("org_tier is only valid for an organization roster")
        return self


class TeamOut(ORMModel):
    id: uuid.UUID
    name: str
    region_id: uuid.UUID
    organization_id: uuid.UUID | None
    org_tier: OrgTier | None
    primary_mode: str | None
    competitive_tier_mp: int
    competitive_tier_br: int
    manager_id: uuid.UUID | None
    logo_url: str | None
    reputation_score: int
    is_active: bool
    created_at: datetime


class InviteMemberIn(BaseModel):
    user_id: uuid.UUID
    role: TeamRole = TeamRole.PLAYER
    in_game_role: str | None = Field(default=None, max_length=50)


class TeamMemberOut(ORMModel):
    id: uuid.UUID
    team_id: uuid.UUID
    user_id: uuid.UUID
    role: TeamRole
    in_game_role: str | None
    is_active: bool
    joined_at: datetime


class PromotePlayerIn(BaseModel):
    to_team_id: uuid.UUID
    new_role: TeamRole = TeamRole.PLAYER
    event_type: str = Field(default="promotion", pattern=r"^(promotion|demotion|role_change)$")


class AchievementIn(BaseModel):
    user_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    title: str = Field(min_length=2, max_length=150)
    category: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=1000)
    tournament_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def one_recipient(self):
        if self.user_id and self.team_id:
            raise ValueError("An achievement can target a player, a team, or the organization—not multiple recipients")
        return self


class HallOfFameIn(BaseModel):
    entity_type: str = Field(pattern=r"^(player|team|organization)$")
    entity_id: uuid.UUID
    title: str = Field(min_length=2, max_length=150)
    citation: str = Field(min_length=10, max_length=1500)


class RetirementIn(BaseModel):
    retired_on: date
    reason: str | None = Field(default=None, max_length=1000)


class ReputationEventIn(BaseModel):
    subject_type: str = Field(pattern=r"^(player|team|organization)$")
    subject_id: uuid.UUID
    delta: int = Field(ge=-25, le=25)
    reason: str = Field(min_length=3, max_length=500)


class OrganizationWorkspaceOut(OrganizationOut):
    can_manage_roster: bool = False


class TeamWorkspaceOut(TeamOut):
    can_manage_roster: bool = False


class RosterMemberOut(TeamMemberOut):
    gamertag: str
    shid: str


class PlayerLookupOut(BaseModel):
    id: uuid.UUID
    shid: str
    gamertag: str
    preferred_mode: str | None
    model_config = {"from_attributes": True}


class TimelineOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    description: str
    from_team_id: uuid.UUID | None
    to_team_id: uuid.UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}
