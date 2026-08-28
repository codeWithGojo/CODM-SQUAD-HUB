"""Protect custom-auth tables from Supabase Data API roles.

Revision ID: 1c7d42e6a911
Revises: 89ac14d6b7c5
Create Date: 2026-08-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "1c7d42e6a911"
down_revision: Union[str, None] = "89ac14d6b7c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


APP_TABLES = (
    "account_reports",
    "account_security_events",
    "achievements",
    "ai_weekly_reviews",
    "audit_logs",
    "blacklist_appeals",
    "blacklist_entries",
    "campaign_contributions",
    "challenges",
    "chat_messages",
    "chat_participants",
    "chat_threads",
    "contracts",
    "crowdfunding_campaigns",
    "drill_pool",
    "hall_of_fame_entries",
    "map_guides",
    "market_value_snapshots",
    "merch_order_items",
    "merch_orders",
    "merch_products",
    "notifications",
    "official_team_results",
    "organization_staff_members",
    "organizations",
    "otp_codes",
    "payment_transactions",
    "performance_metrics",
    "player_match_logs",
    "player_retirements",
    "player_timeline_events",
    "ranking_calculations",
    "ranking_snapshots",
    "regions",
    "reputation_events",
    "scrims",
    "seasons",
    "team_members",
    "team_subscriptions",
    "teams",
    "tournament_disputes",
    "tournament_matches",
    "tournament_organizer_applications",
    "tournament_player_stats",
    "tournament_registrations",
    "tournament_standings",
    "tournaments",
    "training_assignments",
    "training_plans",
    "transfer_offer_events",
    "transfer_offers",
    "transfer_rumours",
    "transfer_watchlists",
    "transfer_windows",
    "users",
    "vod_reviews",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    roles = set(
        bind.execute(
            sa.text("SELECT rolname FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
        ).scalars()
    )
    for table in APP_TABLES:
        op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
        for role in roles:
            op.execute(sa.text(f'REVOKE ALL PRIVILEGES ON TABLE "{table}" FROM "{role}"'))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    for table in APP_TABLES:
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
