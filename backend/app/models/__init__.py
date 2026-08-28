"""Import every model so SQLAlchemy and Alembic share one complete metadata graph."""

from app.models.ai_review import (
    AIWeeklyReview,
    DrillPool,
    PerformanceMetric,
    TrainingAssignment,
    TrainingPlan,
    VODReview,
)
from app.models.commerce import (
    CampaignContribution,
    CrowdfundingCampaign,
    MerchOrder,
    MerchOrderItem,
    MerchProduct,
    PaymentTransaction,
    TeamSubscription,
)
from app.models.communication import ChatMessage, ChatParticipant, ChatThread, Notification
from app.models.competitive import Challenge, OfficialTeamResult, PlayerMatchLog, Scrim
from app.models.governance import BlacklistAppeal, BlacklistEntry, TournamentDispute
from app.models.misc import AccountReport, MapGuide
from app.models.organization_extra import (
    Achievement,
    AuditLog,
    HallOfFameEntry,
    OrganizationStaffMember,
    PlayerRetirement,
    ReputationEvent,
)
from app.models.organizer import TournamentOrganizerApplication
from app.models.ranking import RankingCalculation, RankingSnapshot, Season
from app.models.team import Organization, PlayerTimelineEvent, Team, TeamMember
from app.models.tournament import (
    Tournament,
    TournamentMatch,
    TournamentPlayerStat,
    TournamentRegistration,
    TournamentStanding,
)
from app.models.transfer import (
    Contract,
    MarketValueSnapshot,
    TransferOffer,
    TransferOfferEvent,
    TransferRumour,
    TransferWatchlist,
    TransferWindow,
)
from app.models.user import AccountSecurityEvent, OTPCode, Region, User

__all__ = [name for name in globals() if not name.startswith("_")]
