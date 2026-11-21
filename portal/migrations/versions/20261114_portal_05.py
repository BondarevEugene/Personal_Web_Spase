"""Managed Cloud deployment planning records.

Revision ID: 20261114_portal_05
Revises: 20261114_portal_04
"""
from alembic import op
import sqlalchemy as sa

revision = "20261114_portal_05"
down_revision = "20261114_portal_04"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_cloud_deployments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("mode", sa.String(16), nullable=False),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("request_key", sa.String(100), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("customer_id", "request_key",
                            name="uq_cloud_customer_request"),
    )
    op.create_index("ix_portal_cloud_deployments_customer_id",
                    "portal_cloud_deployments", ["customer_id"])


def downgrade():
    op.drop_index("ix_portal_cloud_deployments_customer_id",
                  table_name="portal_cloud_deployments")
    op.drop_table("portal_cloud_deployments")
