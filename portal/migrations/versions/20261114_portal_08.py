"""Verified Railway BYOC resource bindings.

Revision ID: 20261114_portal_08
Revises: 20261114_portal_07
"""
from alembic import op
import sqlalchemy as sa

revision = "20261114_portal_08"
down_revision = "20261114_portal_07"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_cloud_railway_bindings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("deployment_id", sa.String(36),
                  sa.ForeignKey("portal_cloud_deployments.id"), nullable=False),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("project_id", sa.String(100), nullable=False),
        sa.Column("service_id", sa.String(100), nullable=False),
        sa.Column("environment_id", sa.String(100), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=False),
        sa.Column("last_provider_status", sa.String(60), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("deployment_id", name="uq_cloud_railway_deployment"),
    )
    op.create_index("ix_portal_cloud_railway_bindings_customer_id",
                    "portal_cloud_railway_bindings", ["customer_id"])
    op.create_index("ix_portal_cloud_railway_bindings_deployment_id",
                    "portal_cloud_railway_bindings", ["deployment_id"])


def downgrade():
    op.drop_index("ix_portal_cloud_railway_bindings_deployment_id",
                  table_name="portal_cloud_railway_bindings")
    op.drop_index("ix_portal_cloud_railway_bindings_customer_id",
                  table_name="portal_cloud_railway_bindings")
    op.drop_table("portal_cloud_railway_bindings")
