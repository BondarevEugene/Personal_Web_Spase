"""Bot-specific encrypted secret, invitation and audit tables.

Revision ID: 20261114_portal_09
Revises: 20261114_portal_08
"""
from alembic import op
import sqlalchemy as sa

revision = "20261114_portal_09"
down_revision = "20261114_portal_08"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_bot_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_builder_projects.id"),
                  nullable=False),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("portal_customers.id"),
                  nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("verified_bot_id", sa.String(32)),
        sa.Column("verified_username", sa.String(80)),
        sa.Column("verified_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("rotated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", name="uq_bot_credential_project"),
    )
    op.create_index("ix_portal_bot_credentials_project_id", "portal_bot_credentials", ["project_id"])
    op.create_index("ix_portal_bot_credentials_owner_id", "portal_bot_credentials", ["owner_id"])
    op.create_table(
        "portal_bot_access_grants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_builder_projects.id"),
                  nullable=False),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("portal_customers.id"),
                  nullable=False),
        sa.Column("grantee_id", sa.String(36), sa.ForeignKey("portal_customers.id"),
                  nullable=False),
        sa.Column("role", sa.String(12), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "grantee_id", name="uq_bot_grant_project_customer"),
    )
    op.create_index("ix_portal_bot_access_grants_project_id", "portal_bot_access_grants", ["project_id"])
    op.create_index("ix_portal_bot_access_grants_owner_id", "portal_bot_access_grants", ["owner_id"])
    op.create_index("ix_portal_bot_access_grants_grantee_id", "portal_bot_access_grants", ["grantee_id"])
    op.create_table(
        "portal_bot_access_invitations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_builder_projects.id"),
                  nullable=False),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("portal_customers.id"),
                  nullable=False),
        sa.Column("invited_customer_id", sa.String(36),
                  sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("role", sa.String(12), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime()),
        sa.Column("revoked_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_bot_invitation_hash"),
    )
    op.create_index("ix_portal_bot_access_invitations_project_id",
                    "portal_bot_access_invitations", ["project_id"])
    op.create_index("ix_portal_bot_access_invitations_owner_id",
                    "portal_bot_access_invitations", ["owner_id"])
    op.create_index("ix_portal_bot_access_invitations_invited_customer_id",
                    "portal_bot_access_invitations", ["invited_customer_id"])
    op.create_table(
        "portal_bot_security_audit",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_builder_projects.id"),
                  nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("portal_customers.id"),
                  nullable=False),
        sa.Column("event", sa.String(48), nullable=False),
        sa.Column("target_customer_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_portal_bot_security_audit_project_id",
                    "portal_bot_security_audit", ["project_id"])


def downgrade():
    op.drop_index("ix_portal_bot_security_audit_project_id",
                  table_name="portal_bot_security_audit")
    op.drop_table("portal_bot_security_audit")
    for table, cols in (
        ("portal_bot_access_invitations",
         ("project_id", "owner_id", "invited_customer_id")),
        ("portal_bot_access_grants", ("project_id", "owner_id", "grantee_id")),
        ("portal_bot_credentials", ("project_id", "owner_id")),
    ):
        for col in cols:
            op.drop_index(f"ix_{table}_{col}", table_name=table)
        op.drop_table(table)
