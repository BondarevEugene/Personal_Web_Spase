"""Portal entities. No credentials or sensitive payment card data are persisted."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from portal.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def uuid() -> str:
    return str(uuid4())


class Organization(Base):
    __tablename__ = "portal_organizations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UAH")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, default=utcnow)


class Customer(Base):
    __tablename__ = "portal_customers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    org_id: Mapped[str] = mapped_column(ForeignKey("portal_organizations.id"), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="owner", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utcnow, nullable=False)


class PortalSession(Base):
    __tablename__ = "portal_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("portal_customers.id"), index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utcnow, nullable=False)


class CustomerSettings(Base):
    __tablename__ = "portal_settings"
    customer_id: Mapped[str] = mapped_column(ForeignKey("portal_customers.id"), primary_key=True)
    language: Mapped[str] = mapped_column(String(5), default="ru", nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Europe/Kyiv", nullable=False)
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class RegistrationEvent(Base):
    __tablename__ = "portal_registration_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("portal_customers.id"), index=True, nullable=False)
    org_id: Mapped[str] = mapped_column(ForeignKey("portal_organizations.id"), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="website", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utcnow, nullable=False)


class BillingPlan(Base):
    """Catalog of monthly plans. Paid prices are explicitly configured by owner."""
    __tablename__ = "portal_plans"
    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    price_minor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UAH")
    period_months: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, default=utcnow)
    __table_args__ = (
        CheckConstraint("price_minor IS NULL OR price_minor >= 0", name="ck_portal_plan_nonnegative"),
        CheckConstraint("period_months > 0", name="ck_portal_plan_period"),
    )


class PlanPriceChange(Base):
    """Append-only record of operator catalogue edits (not customer payments)."""
    __tablename__ = "portal_plan_price_changes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    plan_code: Mapped[str] = mapped_column(ForeignKey("portal_plans.code"), nullable=False)
    old_price_minor: Mapped[int | None] = mapped_column(Integer)
    new_price_minor: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, default=utcnow)


class GatewayEvent(Base):
    """Idempotency/audit ledger; only verified provider messages may enter."""
    __tablename__ = "portal_gateway_events"
    __table_args__ = (UniqueConstraint("provider", "event_id", name="uq_portal_gateway_event"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    event_id: Mapped[str] = mapped_column(String(180), nullable=False)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("portal_invoices.id"), nullable=False)
    payment_id: Mapped[str] = mapped_column(ForeignKey("portal_payments.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)


class Subscription(Base):
    __tablename__ = "portal_subscriptions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    org_id: Mapped[str] = mapped_column(ForeignKey("portal_organizations.id"), index=True, nullable=False)
    plan_code: Mapped[str] = mapped_column(String(40), default="free", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="UAH", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utcnow, nullable=False)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Invoice(Base):
    __tablename__ = "portal_invoices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    org_id: Mapped[str] = mapped_column(ForeignKey("portal_organizations.id"), index=True, nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UAH")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    plan_code: Mapped[str | None] = mapped_column(ForeignKey("portal_plans.code"), nullable=True)
    subscription_id: Mapped[str | None] = mapped_column(ForeignKey("portal_subscriptions.id"), nullable=True)
    period_months: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("org_id", "idempotency_key", name="uq_portal_invoice_request"),)


class PaymentRecord(Base):
    __tablename__ = "portal_payments"
    __table_args__ = (UniqueConstraint("provider", "external_id", name="uq_portal_provider_payment"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    org_id: Mapped[str] = mapped_column(ForeignKey("portal_organizations.id"), index=True, nullable=False)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("portal_invoices.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    external_id: Mapped[str] = mapped_column(String(180), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utcnow, nullable=False)


class BuilderProject(Base):
    """Per-customer Telegram workflow draft. No bot tokens or OAuth credentials."""

    __tablename__ = "portal_builder_projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("portal_customers.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario_json: Mapped[str] = mapped_column(Text, nullable=False)
    layout_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, onupdate=utcnow, nullable=False)


class AutomationWorkflow(Base):
    """Owned workflow definition with immutable revision counter."""

    __tablename__ = "portal_automation_workflows"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    customer_id: Mapped[str] = mapped_column(ForeignKey("portal_customers.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    definition_json: Mapped[str] = mapped_column(Text, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    webhook_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)


class AutomationRun(Base):
    """Bounded execution audit: no credential values or raw response bodies."""

    __tablename__ = "portal_automation_runs"
    __table_args__ = (UniqueConstraint("customer_id", "idempotency_key",
                                       name="uq_omni_automation_run_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    workflow_id: Mapped[str] = mapped_column(ForeignKey("portal_automation_workflows.id"),
                                             index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(ForeignKey("portal_customers.id"), index=True, nullable=False)
    workflow_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    trace_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)


class AutomationSchedule(Base):
    """Opt-in interval schedule; worker acquires due runs using database CAS."""

    __tablename__ = "portal_automation_schedules"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    workflow_id: Mapped[str] = mapped_column(
        ForeignKey("portal_automation_workflows.id"), unique=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("portal_customers.id"), index=True, nullable=False)
    interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)


class CloudDeployment(Base):
    """Customer-owned, plan-only deployment intent; contains no secrets."""

    __tablename__ = "portal_cloud_deployments"
    __table_args__ = (
        UniqueConstraint("customer_id", "request_key", name="uq_cloud_customer_request"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("portal_customers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)
    manifest_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    request_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False, default=utcnow)


class CloudOAuthAttempt(Base):
    """Short-lived PKCE state; never store raw state or verifier in plaintext."""

    __tablename__ = "portal_cloud_oauth_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("portal_customers.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    state_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    session_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verifier_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)


class CloudOAuthConnection(Base):
    """Encrypted OAuth credentials, customer-scoped and never returned from API."""

    __tablename__ = "portal_cloud_oauth_connections"
    __table_args__ = (
        UniqueConstraint("customer_id", "provider", name="uq_cloud_oauth_customer_provider"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("portal_customers.id"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    remote_subject: Mapped[str] = mapped_column(String(200), nullable=False)
    remote_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    scopes: Mapped[str] = mapped_column(Text, nullable=False)
    access_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)
