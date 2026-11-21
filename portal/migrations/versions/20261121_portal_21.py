"""Secure Vault and one-time OAuth state persistence.

Revision ID: 20261121_portal_21
Revises: 20261121_portal_20
"""
from alembic import op
import sqlalchemy as sa

revision = "20261121_portal_21"
down_revision = "20261121_portal_20"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_automation_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("connection_id", sa.String(36),
                  sa.ForeignKey("portal_automation_connections.id"),
                  nullable=False, unique=True),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_automation_credentials_customer_id",
                    "portal_automation_credentials", ["customer_id"])
    op.create_table(
        "portal_automation_oauth_states",
        sa.Column("nonce_hash", sa.String(64), primary_key=True),
        sa.Column("connection_id", sa.String(36),
                  sa.ForeignKey("portal_automation_connections.id"), nullable=False),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_portal_automation_oauth_states_connection_id",
                    "portal_automation_oauth_states", ["connection_id"])
    op.create_index("ix_portal_automation_oauth_states_customer_id",
                    "portal_automation_oauth_states", ["customer_id"])


def downgrade():
    op.drop_index("ix_portal_automation_oauth_states_customer_id",
                  table_name="portal_automation_oauth_states")
    op.drop_index("ix_portal_automation_oauth_states_connection_id",
                  table_name="portal_automation_oauth_states")
    op.drop_table("portal_automation_oauth_states")
    op.drop_index("ix_portal_automation_credentials_customer_id",
                  table_name="portal_automation_credentials")
    op.drop_table("portal_automation_credentials")
