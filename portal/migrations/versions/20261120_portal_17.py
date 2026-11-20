"""Moderated creative copy for service and case pages.

Revision ID: 20261120_portal_17
Revises: 20261120_portal_16
"""
from alembic import op
import sqlalchemy as sa

revision = "20261120_portal_17"
down_revision = "20261120_portal_16"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_public_page_revisions",
        sa.Column("page_key", sa.String(160), primary_key=True),
        sa.Column("draft_title", sa.String(180), nullable=False),
        sa.Column("draft_summary", sa.String(800), nullable=False),
        sa.Column("published_title", sa.String(180)),
        sa.Column("published_summary", sa.String(800)),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("scheduled_for", sa.DateTime()),
        sa.Column("updated_by_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("portal_public_page_revisions")
