"""Store PKCE verifier encrypted with OAuth state.

Revision ID: 20261121_portal_22
Revises: 20261121_portal_21
"""
import sqlalchemy as sa
from alembic import op

revision = "20261121_portal_22"
down_revision = "20261121_portal_21"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("portal_automation_oauth_states",
                  sa.Column("pkce_verifier_ciphertext", sa.LargeBinary(), nullable=True))


def downgrade():
    op.drop_column("portal_automation_oauth_states", "pkce_verifier_ciphertext")
