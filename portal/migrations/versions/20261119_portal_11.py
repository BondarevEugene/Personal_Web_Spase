"""Client support desk: organization-scoped tickets and discussion.

Revision ID: 20261119_portal_11
Revises: 20261114_portal_10
"""
from alembic import op
import sqlalchemy as sa

revision = "20261119_portal_11"
down_revision = "20261114_portal_10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_support_tickets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("portal_organizations.id"), nullable=False),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("subject", sa.String(160), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_support_tickets_org_id", "portal_support_tickets", ["org_id"])
    op.create_table(
        "portal_support_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ticket_id", sa.String(36), sa.ForeignKey("portal_support_tickets.id"), nullable=False),
        sa.Column("author_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_support_messages_ticket_id", "portal_support_messages", ["ticket_id"])


def downgrade():
    op.drop_index("ix_portal_support_messages_ticket_id", table_name="portal_support_messages")
    op.drop_table("portal_support_messages")
    op.drop_index("ix_portal_support_tickets_org_id", table_name="portal_support_tickets")
    op.drop_table("portal_support_tickets")
