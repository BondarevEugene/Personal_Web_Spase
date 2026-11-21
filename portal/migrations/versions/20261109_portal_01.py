"""Initial customer portal schema: accounts, tenants, sessions and billing ledger.

Revision ID: 20261109_portal_01
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "20261109_portal_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("portal_organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("portal_customers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("portal_organizations.id"), nullable=False),
        sa.Column("email", sa.String(254), unique=True, nullable=False),
        sa.Column("username", sa.String(32), unique=True, nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_portal_customers_org_id", "portal_customers", ["org_id"])
    op.create_table("portal_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_portal_sessions_customer_id", "portal_sessions", ["customer_id"])
    op.create_table("portal_settings",
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("portal_customers.id"), primary_key=True),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False),
        sa.Column("marketing_opt_in", sa.Boolean(), nullable=False))
    op.create_table("portal_registration_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("portal_customers.id"), nullable=False),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("portal_organizations.id"), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_portal_registration_events_customer_id", "portal_registration_events", ["customer_id"])
    op.create_index("ix_portal_registration_events_org_id", "portal_registration_events", ["org_id"])
    op.create_table("portal_subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("portal_organizations.id"), nullable=False),
        sa.Column("plan_code", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_portal_subscriptions_org_id", "portal_subscriptions", ["org_id"])
    op.create_table("portal_invoices",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("portal_organizations.id"), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_portal_invoices_org_id", "portal_invoices", ["org_id"])
    op.create_table("portal_payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("portal_organizations.id"), nullable=False),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("portal_invoices.id"), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("external_id", sa.String(180), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("provider", "external_id", name="uq_portal_provider_payment"))
    op.create_index("ix_portal_payments_org_id", "portal_payments", ["org_id"])


def downgrade():
    op.drop_table("portal_payments")
    op.drop_table("portal_invoices")
    op.drop_table("portal_subscriptions")
    op.drop_table("portal_registration_events")
    op.drop_table("portal_settings")
    op.drop_table("portal_sessions")
    op.drop_table("portal_customers")
    op.drop_table("portal_organizations")
