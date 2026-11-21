"""Provisioning request ledger.

Revision ID: 20261114_portal_07
Revises: 20261114_portal_06
"""
from alembic import op
import sqlalchemy as sa

revision = "20261114_portal_07"
down_revision = "20261114_portal_06"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_cloud_provision_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("deployment_id", sa.String(36),
                  sa.ForeignKey("portal_cloud_deployments.id"), nullable=False),
        sa.Column("request_key", sa.String(100), nullable=False),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("manifest_snapshot", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("mode", sa.String(12), nullable=False),
        sa.Column("approval_note", sa.String(300), nullable=True),
        sa.Column("provider_project_id", sa.String(100), nullable=True),
        sa.Column("provider_service_id", sa.String(100), nullable=True),
        sa.Column("provider_deployment_id", sa.String(100), nullable=True),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("customer_id", "request_key",
                            name="uq_cloud_provision_customer_key"))
    op.create_index("ix_portal_cloud_provision_jobs_customer_id",
                    "portal_cloud_provision_jobs", ["customer_id"])
    op.create_index("ix_portal_cloud_provision_jobs_deployment_id",
                    "portal_cloud_provision_jobs", ["deployment_id"])
    op.create_table(
        "portal_cloud_provision_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36),
                  sa.ForeignKey("portal_cloud_provision_jobs.id"), nullable=False),
        sa.Column("code", sa.String(70), nullable=False),
        sa.Column("message", sa.String(300), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_portal_cloud_provision_events_job_id",
                    "portal_cloud_provision_events", ["job_id"])


def downgrade():
    op.drop_index("ix_portal_cloud_provision_events_job_id",
                  table_name="portal_cloud_provision_events")
    op.drop_table("portal_cloud_provision_events")
    op.drop_index("ix_portal_cloud_provision_jobs_deployment_id",
                  table_name="portal_cloud_provision_jobs")
    op.drop_index("ix_portal_cloud_provision_jobs_customer_id",
                  table_name="portal_cloud_provision_jobs")
    op.drop_table("portal_cloud_provision_jobs")
