"""
Shared enums. Kept in one place so the same vocabulary is used
everywhere (models, schemas, business logic) instead of magic strings.
"""
import enum


class Mode(str, enum.Enum):
    MP = "MP"
    BR = "BR"


class TeamRole(str, enum.Enum):
    MANAGER = "manager"
    PLAYER = "player"


class CompetitiveTier(int, enum.Enum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class OrgTier(str, enum.Enum):
    T1_FIRST_TEAM = "T1"
    T2_SECOND_TEAM = "T2"
    T3_ACADEMY = "T3"
    T4_DEVELOPMENT = "T4"


class MatchResult(str, enum.Enum):
    WIN = "win"
    LOSS = "loss"


class ChallengeStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    DISPUTED = "disputed"


class ScrimStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AIReviewStatus(str, enum.Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
    SKIPPED_NO_DATA = "skipped_no_data"  # player logged zero matches that week


class PlayerContractStatus(str, enum.Enum):
    UNDER_CONTRACT = "under_contract"
    TRANSFER_LISTED = "transfer_listed"
    LOAN_LISTED = "loan_listed"
    FREE_AGENT = "free_agent"
    ON_LOAN = "on_loan"


class TransferOfferType(str, enum.Enum):
    PERMANENT = "permanent"
    LOAN = "loan"
    FREE_SIGNING = "free_signing"


class TransferOfferStatus(str, enum.Enum):
    PENDING_CLUB_REVIEW = "pending_club_review"
    COUNTERED = "countered"
    REJECTED_BY_CLUB = "rejected_by_club"
    PENDING_PLAYER_REVIEW = "pending_player_review"
    REJECTED_BY_PLAYER = "rejected_by_player"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ELITE = "elite"
# Add to app/models/enums.py

class TournamentOrganizerStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"