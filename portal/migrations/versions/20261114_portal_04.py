"""Automation workflows and tenant-safe run ledger.

Revision ID: 20261114_portal_04
Revises: 20261113_portal_03
"""
from alembic import op
import sqlalchemy as sa

revision = "20261114_portal_04"
down_revision = "20261113_portal_03"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_automation_workflows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("definition_json", sa.Text(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("webhook_token_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_portal_automation_workflows_customer_id",
                    "portal_automation_workflows", ["customer_id"])
    op.create_table(
        "portal_automation_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_id", sa.String(36),
                  sa.ForeignKey("portal_automation_workflows.id"), nullable=False),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("workflow_revision", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("mode", sa.String(10), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=True),
        sa.Column("trace_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("customer_id", "idempotency_key",
                            name="uq_omni_automation_run_key"))
    op.create_index("ix_portal_automation_runs_customer_id",
                    "portal_automation_runs", ["customer_id"])
    op.create_index("ix_portal_automation_runs_workflow_id",
                    "portal_automation_runs", ["workflow_id"])


def downgrade():
    op.drop_index("ix_portal_automation_runs_workflow_id",
                  table_name="portal_automation_runs")
    op.drop_index("ix_portal_automation_runs_customer_id",
                  table_name="portal_automation_runs")
    op.drop_table("portal_automation_runs")
    op.drop_index("ix_portal_automation_workflows_customer_id",
                  table_name="portal_automation_workflows")
    op.drop_table("portal_automation_workflows")
