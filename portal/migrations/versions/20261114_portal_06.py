"""Railway OAuth PKCE and encrypted provider connections.

Revision ID: 20261114_portal_06
Revises: 20261114_portal_05
"""
from alembic import op
import sqlalchemy as sa

revision = "20261114_portal_06"
down_revision = "20261114_portal_05"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_cloud_oauth_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("state_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("session_hash", sa.String(64), nullable=False),
        sa.Column("verifier_ciphertext", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_portal_cloud_oauth_attempts_customer_id",
                    "portal_cloud_oauth_attempts", ["customer_id"])
    op.create_table(
        "portal_cloud_oauth_connections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("remote_subject", sa.String(200), nullable=False),
        sa.Column("remote_name", sa.String(200), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("access_ciphertext", sa.Text(), nullable=False),
        sa.Column("refresh_ciphertext", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("customer_id", "provider",
                            name="uq_cloud_oauth_customer_provider"))
    op.create_index("ix_portal_cloud_oauth_connections_customer_id",
                    "portal_cloud_oauth_connections", ["customer_id"])


def downgrade():
    op.drop_index("ix_portal_cloud_oauth_connections_customer_id",
                  table_name="portal_cloud_oauth_connections")
    op.drop_table("portal_cloud_oauth_connections")
    op.drop_index("ix_portal_cloud_oauth_attempts_customer_id",
                  table_name="portal_cloud_oauth_attempts")
    op.drop_table("portal_cloud_oauth_attempts")
