"""Versioned text deliverables, explicit approval and in-app notices.

Revision ID: 20261119_portal_14
Revises: 20261119_portal_13
"""
from alembic import op
import sqlalchemy as sa

revision = "20261119_portal_14"
down_revision = "20261119_portal_13"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_client_project_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_client_projects.id"), nullable=False),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("document_kind", sa.String(32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "document_kind", "version",
                            name="uq_client_project_document_version"),
    )
    op.create_index("ix_portal_client_project_documents_project_id",
                    "portal_client_project_documents", ["project_id"])
    op.create_table(
        "portal_client_project_approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("portal_client_project_documents.id"), nullable=False),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("portal_organizations.id"), nullable=False),
        sa.Column("approved_by_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("document_id", "org_id", name="uq_client_document_org_approval"),
    )
    op.create_index("ix_portal_client_project_approvals_document_id",
                    "portal_client_project_approvals", ["document_id"])
    op.create_table(
        "portal_client_project_notifications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recipient_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_client_projects.id"), nullable=False),
        sa.Column("message", sa.String(250), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_portal_client_project_notifications_recipient_id",
                    "portal_client_project_notifications", ["recipient_id"])


def downgrade():
    op.drop_index("ix_portal_client_project_notifications_recipient_id",
                  table_name="portal_client_project_notifications")
    op.drop_table("portal_client_project_notifications")
    op.drop_index("ix_portal_client_project_approvals_document_id",
                  table_name="portal_client_project_approvals")
    op.drop_table("portal_client_project_approvals")
    op.drop_index("ix_portal_client_project_documents_project_id",
                  table_name="portal_client_project_documents")
    op.drop_table("portal_client_project_documents")
