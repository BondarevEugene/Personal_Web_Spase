"""Subscription catalog, invoice snapshots, payment verification and ledger.

Revision ID: 20261109_portal_02
Revises: 20261109_portal_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20261109_portal_02"
down_revision = "20261109_portal_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("portal_plans",
        sa.Column("code", sa.String(40), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("price_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("period_months", sa.Integer(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("price_minor IS NULL OR price_minor >= 0", name="ck_portal_plan_nonnegative"),
        sa.CheckConstraint("period_months > 0", name="ck_portal_plan_period"))
    op.create_table("portal_plan_price_changes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_code", sa.String(40), sa.ForeignKey("portal_plans.code"), nullable=False),
        sa.Column("old_price_minor", sa.Integer(), nullable=True),
        sa.Column("new_price_minor", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("actor", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.add_column("portal_subscriptions", sa.Column("current_period_start", sa.DateTime(), nullable=True))
    op.add_column("portal_subscriptions", sa.Column("current_period_end", sa.DateTime(), nullable=True))
    op.add_column("portal_subscriptions", sa.Column("cancel_at_period_end", sa.Boolean(), server_default=sa.false(), nullable=False))
    # SQLite needs recreate/batch mode to add FKs to an existing invoice table.
    # Alembic uses native ALTERs for PostgreSQL and copy-and-move on SQLite.
    with op.batch_alter_table("portal_invoices") as batch:
        batch.add_column(sa.Column("plan_code", sa.String(40), nullable=True))
        batch.add_column(sa.Column("subscription_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("period_months", sa.Integer(), server_default="1", nullable=False))
        batch.add_column(sa.Column("idempotency_key", sa.String(80), nullable=True))
        batch.add_column(sa.Column("due_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("paid_at", sa.DateTime(), nullable=True))
        batch.create_foreign_key("fk_portal_invoice_plan", "portal_plans", ["plan_code"], ["code"])
        batch.create_foreign_key("fk_portal_invoice_subscription", "portal_subscriptions",
                                 ["subscription_id"], ["id"])
    op.create_index("uq_portal_invoice_request", "portal_invoices", ["org_id", "idempotency_key"], unique=True)
    op.add_column("portal_payments", sa.Column("verified_at", sa.DateTime(), nullable=True))
    op.create_table("portal_gateway_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("event_id", sa.String(180), nullable=False),
        sa.Column("invoice_id", sa.String(36), sa.ForeignKey("portal_invoices.id"), nullable=False),
        sa.Column("payment_id", sa.String(36), sa.ForeignKey("portal_payments.id"), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("provider", "event_id", name="uq_portal_gateway_event"))
    # Seed catalog as unavailable. The owner must set real prices before plans can be ordered.
    plans = sa.table("portal_plans",
        sa.column("code", sa.String), sa.column("name", sa.String),
        sa.column("description", sa.String), sa.column("price_minor", sa.Integer),
        sa.column("currency", sa.String), sa.column("period_months", sa.Integer),
        sa.column("is_public", sa.Boolean), sa.column("is_enabled", sa.Boolean),
        sa.column("created_at", sa.DateTime))
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    op.bulk_insert(plans, [
        dict(code="free", name="Free", description="Бесплатная регистрация и базовый доступ",
             price_minor=0, currency="UAH", period_months=1,
             is_public=True, is_enabled=True, created_at=now),
        dict(code="start", name="Start", description="Платный уровень — функции уточняются",
             price_minor=None, currency="UAH", period_months=1,
             is_public=True, is_enabled=False, created_at=now),
        dict(code="growth", name="Growth", description="Платный уровень — функции уточняются",
             price_minor=None, currency="UAH", period_months=1,
             is_public=True, is_enabled=False, created_at=now),
        dict(code="business", name="Business", description="Платный уровень — функции уточняются",
             price_minor=None, currency="UAH", period_months=1,
             is_public=True, is_enabled=False, created_at=now),
    ])


def downgrade():
    op.drop_table("portal_gateway_events")
    op.drop_column("portal_payments", "verified_at")
    op.drop_index("uq_portal_invoice_request", table_name="portal_invoices")
    with op.batch_alter_table("portal_invoices") as batch:
        batch.drop_constraint("fk_portal_invoice_subscription", type_="foreignkey")
        batch.drop_constraint("fk_portal_invoice_plan", type_="foreignkey")
        for column in ("paid_at", "due_at", "idempotency_key", "period_months",
                       "subscription_id", "plan_code"):
            batch.drop_column(column)
    for column in ("cancel_at_period_end", "current_period_end", "current_period_start"):
        op.drop_column("portal_subscriptions", column)
    op.drop_table("portal_plan_price_changes")
    op.drop_table("portal_plans")
