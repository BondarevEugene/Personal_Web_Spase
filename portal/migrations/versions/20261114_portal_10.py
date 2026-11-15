"""Immutable owner-reviewed release intent; never billable.

Revision ID: 20261114_portal_10
Revises: 20261114_portal_09
"""
from alembic import op
import sqlalchemy as sa

revision = "20261114_portal_10"
down_revision = "20261114_portal_09"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_cloud_release_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("bot_project_id", sa.String(36), sa.ForeignKey("portal_builder_projects.id"), nullable=False),
        sa.Column("cloud_plan_id", sa.String(36), sa.ForeignKey("portal_cloud_deployments.id"), nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("artifact_image", sa.String(240), nullable=False),
        sa.Column("plan_hash", sa.String(64), nullable=False),
        sa.Column("credential_fingerprint", sa.String(64), nullable=False),
        sa.Column("revision_hash", sa.String(64), nullable=False),
        sa.Column("review_hash", sa.String(64), nullable=False),
        sa.Column("budget_cap_usd", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("cancelled_at", sa.DateTime()),
        sa.UniqueConstraint("owner_id", "request_key", name="uq_cloud_release_request"),
    )
    for name in ("owner_id", "bot_project_id", "cloud_plan_id"):
        op.create_index("ix_portal_cloud_release_reviews_" + name,
                        "portal_cloud_release_reviews", [name])


def downgrade():
    for name in ("cloud_plan_id", "bot_project_id", "owner_id"):
        op.drop_index("ix_portal_cloud_release_reviews_" + name,
                      table_name="portal_cloud_release_reviews")
    op.drop_table("portal_cloud_release_reviews")
