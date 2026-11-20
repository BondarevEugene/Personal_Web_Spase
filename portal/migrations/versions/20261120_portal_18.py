"""Project task hierarchy and time tracking.

Revision ID: 20261120_portal_18
Revises: 20261120_portal_17
"""
from alembic import op
import sqlalchemy as sa

revision = "20261120_portal_18"
down_revision = "20261120_portal_17"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_client_project_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_client_projects.id"), nullable=False),
        sa.Column("parent_id", sa.String(36), sa.ForeignKey("portal_client_project_tasks.id")),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("assignee_id", sa.String(36), sa.ForeignKey("portal_customers.id")),
        sa.Column("start_on", sa.DateTime()),
        sa.Column("due_on", sa.DateTime()),
        sa.Column("estimate_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("estimate_minutes >= 0", name="ck_project_task_estimate"),
    )
    op.create_index("ix_portal_client_project_tasks_project_id", "portal_client_project_tasks", ["project_id"])
    op.create_table(
        "portal_client_project_time_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_id", sa.String(36), sa.ForeignKey("portal_client_project_tasks.id"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("minutes > 0 AND minutes <= 1440", name="ck_project_time_minutes"),
    )
    op.create_index("ix_portal_client_project_time_entries_task_id", "portal_client_project_time_entries", ["task_id"])


def downgrade():
    op.drop_index("ix_portal_client_project_time_entries_task_id", table_name="portal_client_project_time_entries")
    op.drop_table("portal_client_project_time_entries")
    op.drop_index("ix_portal_client_project_tasks_project_id", table_name="portal_client_project_tasks")
    op.drop_table("portal_client_project_tasks")
