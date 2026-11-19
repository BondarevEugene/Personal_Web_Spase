"""Real client project lifecycle with milestones and immutable events.

Revision ID: 20261119_portal_13
Revises: 20261119_portal_12
"""
from alembic import op
import sqlalchemy as sa

revision = "20261119_portal_13"
down_revision = "20261119_portal_12"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_client_projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("portal_organizations.id"), nullable=False),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("assigned_to_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_client_projects_org_id", "portal_client_projects", ["org_id"])
    op.create_table(
        "portal_client_project_milestones",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_client_projects.id"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_client_project_milestones_project_id",
                    "portal_client_project_milestones", ["project_id"])
    op.create_table(
        "portal_client_project_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_client_projects.id"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_client_project_events_project_id",
                    "portal_client_project_events", ["project_id"])


def downgrade():
    op.drop_index("ix_portal_client_project_events_project_id", table_name="portal_client_project_events")
    op.drop_table("portal_client_project_events")
    op.drop_index("ix_portal_client_project_milestones_project_id",
                  table_name="portal_client_project_milestones")
    op.drop_table("portal_client_project_milestones")
    op.drop_index("ix_portal_client_projects_org_id", table_name="portal_client_projects")
    op.drop_table("portal_client_projects")
