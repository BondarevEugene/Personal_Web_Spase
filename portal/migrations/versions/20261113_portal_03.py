"""Persist authenticated Graph Studio drafts without storing credentials.

Revision ID: 20261113_portal_03
Revises: 20261109_portal_02
"""
from alembic import op
import sqlalchemy as sa

revision = "20261113_portal_03"
down_revision = "20261109_portal_02"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_builder_projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("scenario_json", sa.Text(), nullable=False),
        sa.Column("layout_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_builder_projects_customer_id",
                    "portal_builder_projects", ["customer_id"])


def downgrade():
    op.drop_index("ix_portal_builder_projects_customer_id",
                  table_name="portal_builder_projects")
    op.drop_table("portal_builder_projects")
