"""
Shared logic for moving a player from one team to another — used by
promotions/demotions within an organization
once a deal completes. Centralized here so both call sites can't drift
out of sync on the rule that matters most: personal competitive stats,
rankings, and market value NEVER reset on a move — only which team a
player is attached to changes (locked decision).
"""
import uuid

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models.team import TeamMember, PlayerTimelineEvent
from app.models.enums import TeamRole
from app.models.transfer import Contract


def move_player_to_team(
    db: Session,
    *,
    user_id: uuid.UUID,
    to_team_id: uuid.UUID,
    new_role: TeamRole,
    event_type: str,
    description: str,
) -> TeamMember:
    """
    Deactivates the player's current active membership (if any) on their
    old team, creates a new active membership on the destination team,
    and writes a PlayerTimelineEvent describing the move.

    Deliberately does NOT touch: PlayerMatchLog rows, AIWeeklyReview rows,
    MarketValueSnapshot rows, or any individual-leaderboard-relevant data.
    Those all key off user_id directly, not team_id, so they survive a
    team move untouched by construction — nothing to "carry over" because
    nothing was ever team-scoped in the first place.
    """
    old_membership = (
        db.query(TeamMember)
        .filter(
            TeamMember.user_id == user_id,
            TeamMember.is_active.is_(True),
            TeamMember.role.in_([TeamRole.PLAYER, TeamRole.SUBSTITUTE]),
        )
        .first()
    )
    from_team_id = old_membership.team_id if old_membership else None

    if old_membership:
        old_membership.is_active = False
        old_membership.left_at = utcnow()

    new_membership = TeamMember(
        team_id=to_team_id,
        user_id=user_id,
        role=new_role,
        is_active=True,
    )
    db.add(new_membership)

    contract = db.query(Contract).filter(Contract.player_id == user_id, Contract.is_active.is_(True)).first()
    if contract:
        contract.team_id = to_team_id

    db.add(
        PlayerTimelineEvent(
            user_id=user_id,
            event_type=event_type,
            description=description,
            from_team_id=from_team_id,
            to_team_id=to_team_id,
        )
    )

    db.commit()
    db.refresh(new_membership)
    return new_membership
