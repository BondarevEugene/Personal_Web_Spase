"""Operator-reviewed support lifecycle and audit trail.

Revision ID: 20261119_portal_12
Revises: 20261119_portal_11
"""
from alembic import op
import sqlalchemy as sa

revision = "20261119_portal_12"
down_revision = "20261119_portal_11"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("portal_support_tickets") as batch:
        batch.add_column(sa.Column("assigned_to_id", sa.String(36), nullable=True))
        batch.create_foreign_key(
            "fk_support_tickets_assigned_to",
            "portal_customers",
            ["assigned_to_id"],
            ["id"],
        )
    op.create_table(
        "portal_support_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ticket_id", sa.String(36), sa.ForeignKey("portal_support_tickets.id"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("old_status", sa.String(30), nullable=False),
        sa.Column("new_status", sa.String(30), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_support_events_ticket_id", "portal_support_events", ["ticket_id"])


def downgrade():
    op.drop_index("ix_portal_support_events_ticket_id", table_name="portal_support_events")
    op.drop_table("portal_support_events")
    with op.batch_alter_table("portal_support_tickets") as batch:
        batch.drop_constraint("fk_support_tickets_assigned_to", type_="foreignkey")
        batch.drop_column("assigned_to_id")
