"""Automation connection registry and append-only audit.

Revision ID: 20261121_portal_20
Revises: 20261120_portal_18
"""
from alembic import op
import sqlalchemy as sa

revision = "20261121_portal_20"
down_revision = "20261120_portal_18"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_automation_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("customer_id", "provider", "label",
                            name="uq_automation_connection_label"),
    )
    op.create_index("ix_portal_automation_connections_customer_id",
                    "portal_automation_connections", ["customer_id"])
    op.create_table(
        "portal_automation_connection_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("connection_id", sa.String(36),
                  sa.ForeignKey("portal_automation_connections.id"), nullable=False),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("actor_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_automation_connection_events_connection_id",
                    "portal_automation_connection_events", ["connection_id"])
    op.create_index("ix_portal_automation_connection_events_customer_id",
                    "portal_automation_connection_events", ["customer_id"])


def downgrade():
    op.drop_index("ix_portal_automation_connection_events_customer_id",
                  table_name="portal_automation_connection_events")
    op.drop_index("ix_portal_automation_connection_events_connection_id",
                  table_name="portal_automation_connection_events")
    op.drop_table("portal_automation_connection_events")
    op.drop_index("ix_portal_automation_connections_customer_id",
                  table_name="portal_automation_connections")
    op.drop_table("portal_automation_connections")
