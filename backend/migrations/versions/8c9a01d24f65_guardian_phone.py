"""Record a guardian contact for new minor accounts.

Revision ID: 8c9a01d24f65
Revises: 6f2d8f31a4c0
"""
from alembic import op
import sqlalchemy as sa

revision = "8c9a01d24f65"
down_revision = "6f2d8f31a4c0"
branch_labels = None
depends_on = None


def upgrade():
    # The legacy initial revision creates current metadata on a fresh install.
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "guardian_phone" not in columns:
        op.add_column("users", sa.Column("guardian_phone", sa.String(20), nullable=True))


def downgrade():
    op.drop_column("users", "guardian_phone")
