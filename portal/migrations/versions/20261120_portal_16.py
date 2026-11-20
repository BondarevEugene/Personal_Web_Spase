"""Editable public journal drafts and separately published snapshots.

Revision ID: 20261120_portal_16
Revises: 20261119_portal_15
"""
from alembic import op
import sqlalchemy as sa

revision = "20261120_portal_16"
down_revision = "20261119_portal_15"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_public_article_revisions",
        sa.Column("slug", sa.String(120), primary_key=True),
        sa.Column("draft_title", sa.String(180), nullable=False),
        sa.Column("draft_excerpt", sa.String(450), nullable=False),
        sa.Column("draft_sections", sa.Text(), nullable=False),
        sa.Column("published_title", sa.String(180)),
        sa.Column("published_excerpt", sa.String(450)),
        sa.Column("published_sections", sa.Text()),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("updated_by_id", sa.String(36), sa.ForeignKey("portal_customers.id")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "portal_public_search_metrics",
        sa.Column("date", sa.String(10), primary_key=True),
        sa.Column("path", sa.String(240), primary_key=True),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False),
        sa.Column("position", sa.Float(), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("clicks >= 0 AND impressions >= clicks",
                           name="ck_search_metric_valid_counts"),
    )


def downgrade():
    op.drop_table("portal_public_search_metrics")
    op.drop_table("portal_public_article_revisions")
