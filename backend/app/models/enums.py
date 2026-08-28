"""Shared domain enums used by models, schemas, services, and API responses."""

from __future__ import annotations

import enum


class Mode(str, enum.Enum):
    MP = "MP"
    BR = "BR"


class TeamRole(str, enum.Enum):
    MANAGER = "manager"
    PLAYER = "player"
    SUBSTITUTE = "substitute"


class CompetitiveTier(int, enum.Enum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3
    TIER_4 = 4


class OrgTier(str, enum.Enum):
    T1_FIRST_TEAM = "T1"
    T2_SECOND_TEAM = "T2"
    T3_ACADEMY = "T3"
    T4_DEVELOPMENT = "T4"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class CareerStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"


class OrgStaffRole(str, enum.Enum):
    OWNER = "owner"
    MANAGER = "manager"
    HEAD_COACH = "head_coach"
    COACH = "coach"
    ANALYST = "analyst"
    SCOUT = "scout"
    MEDIA = "media"
    FINANCE = "finance"
    CUSTOM = "custom"


class MatchResult(str, enum.Enum):
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"


class ChallengeStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class ScrimStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TournamentOrganizerStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class TournamentStatus(str, enum.Enum):
    DRAFT = "draft"
    REGISTRATION = "registration"
    ROSTER_LOCKED = "roster_locked"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TournamentFormat(str, enum.Enum):
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    ROUND_ROBIN = "round_robin"
    GROUPS_THEN_KNOCKOUT = "groups_then_knockout"
    BR_POINTS = "br_points"


class RegistrationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    DISQUALIFIED = "disqualified"


class TournamentMatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    READY = "ready"
    LIVE = "live"
    REPORTED = "reported"
    DISPUTED = "disputed"
    VERIFIED = "verified"
    FORFEIT = "forfeit"
    CANCELLED = "cancelled"


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class BlacklistStatus(str, enum.Enum):
    ACTIVE = "active"
    APPEALED = "appealed"
    EXPIRED = "expired"
    REVOKED = "revoked"


class BlacklistSubjectType(str, enum.Enum):
    USER = "user"
    TEAM = "team"
    ORGANIZATION = "organization"


class SanctionType(str, enum.Enum):
    WARNING = "warning"
    TOURNAMENT_BAN = "tournament_ban"
    TRANSFER_BAN = "transfer_ban"
    CHAT_RESTRICTION = "chat_restriction"
    PLATFORM_BAN = "platform_ban"


class RankingEntityType(str, enum.Enum):
    PLAYER = "player"
    TEAM = "team"
    ORGANIZATION = "organization"


class RankingScope(str, enum.Enum):
    NATIONAL = "national"
    REGIONAL = "regional"
    CONTINENTAL = "continental"


class AIReviewStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    SKIPPED_NO_DATA = "skipped_no_data"


class TrainingAssignmentStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class PlayerContractStatus(str, enum.Enum):
    UNDER_CONTRACT = "under_contract"
    TRANSFER_LISTED = "transfer_listed"
    LOAN_LISTED = "loan_listed"
    FREE_AGENT = "free_agent"
    ON_LOAN = "on_loan"
    EXPIRED = "expired"
    TERMINATED = "terminated"


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
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RumourReliability(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIRMED = "confirmed"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ELITE = "elite"


class BillingCycle(str, enum.Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class PaymentStatus(str, enum.Enum):
    INITIALIZED = "initialized"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    ABANDONED = "abandoned"
    REFUNDED = "refunded"


class PaymentPurpose(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    TOURNAMENT_ENTRY = "tournament_entry"
    CROWDFUNDING = "crowdfunding"
    MERCH = "merch"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    FUNDED = "funded"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class OrderStatus(str, enum.Enum):
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class NotificationType(str, enum.Enum):
    SYSTEM = "system"
    TOURNAMENT = "tournament"
    MATCH = "match"
    RANKING = "ranking"
    TRANSFER = "transfer"
    CHAT = "chat"
    AI_REVIEW = "ai_review"
    PAYMENT = "payment"
    MODERATION = "moderation"


class ChatThreadType(str, enum.Enum):
    DIRECT = "direct"
    TEAM = "team"
    TOURNAMENT = "tournament"
    SUPPORT = "support"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    VERIFY = "verify"
    BAN = "ban"
    UNBAN = "unban"
    LOGIN = "login"
