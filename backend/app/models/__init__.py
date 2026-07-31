"""
Import every model here so `Base.metadata.create_all()` (and Alembic's
autogenerate) discovers all tables from a single import of this package.
"""
from app.models.user import Region, User, OTPCode
from app.models.team import Organization, Team, TeamMember, PlayerTimelineEvent
from app.models.competitive import (
    OfficialTeamResult,
    Challenge,
    Scrim,
    PlayerMatchLog,
)
from app.models.ai_review import VODReview, DrillPool, AIWeeklyReview
from app.models.transfer import Contract, TransferOffer, MarketValueSnapshot, TransferWindow
from app.models.misc import MapGuide, Subscription, AccountReport

__all__ = [
    "Region", "User", "OTPCode",
    "Organization", "Team", "TeamMember", "PlayerTimelineEvent",
    "OfficialTeamResult", "Challenge", "Scrim", "PlayerMatchLog",
    "VODReview", "DrillPool", "AIWeeklyReview",
    "Contract", "TransferOffer", "MarketValueSnapshot", "TransferWindow",
    "MapGuide", "Subscription", "AccountReport",
]
from app.models.organizer import TournamentOrganizerApplication
# ...and add "TournamentOrganizerApplication" to the __all__ list