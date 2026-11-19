"""Bounded private project files (PDF, PNG, JPEG, TXT).

Revision ID: 20261119_portal_15
Revises: 20261119_portal_14
"""
from alembic import op
import sqlalchemy as sa

revision = "20261119_portal_15"
down_revision = "20261119_portal_14"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "portal_client_project_attachments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("portal_client_projects.id"), nullable=False),
        sa.Column("uploaded_by_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("filename", sa.String(120), nullable=False),
        sa.Column("mime_type", sa.String(70), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("size_bytes > 0 AND size_bytes <= 2097152",
                           name="ck_project_attachment_size"),
    )
    op.create_index("ix_portal_client_project_attachments_project_id",
                    "portal_client_project_attachments", ["project_id"])


def downgrade():
    op.drop_index("ix_portal_client_project_attachments_project_id",
                  table_name="portal_client_project_attachments")
    op.drop_table("portal_client_project_attachments")
