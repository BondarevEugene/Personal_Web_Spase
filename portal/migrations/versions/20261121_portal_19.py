"""Growth lead intake, attribution and delivery audit.

Revision ID: 20261121_portal_19
Revises: 20261120_portal_18
"""

import sqlalchemy as sa
from alembic import op

revision = "20261121_portal_19"
down_revision = "20261120_portal_18"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_growth_leads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("contact", sa.String(200), nullable=False),
        sa.Column("topic", sa.String(160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_path", sa.String(200), nullable=False),
        sa.Column("utm_source", sa.String(80), nullable=False),
        sa.Column("utm_medium", sa.String(80), nullable=False),
        sa.Column("utm_campaign", sa.String(80), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("telegram_status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_portal_growth_leads_created_at",
        "portal_growth_leads", ["created_at"],
    )
    op.create_index(
        "ix_portal_growth_leads_status",
        "portal_growth_leads", ["status"],
    )


def downgrade():
    op.drop_index("ix_portal_growth_leads_status", table_name="portal_growth_leads")
    op.drop_index("ix_portal_growth_leads_created_at", table_name="portal_growth_leads")
    op.drop_table("portal_growth_leads")
