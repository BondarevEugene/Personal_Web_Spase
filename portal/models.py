"""Portal entities. No credentials or sensitive payment card data are persisted."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
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


class Subscription(Base):
    __tablename__ = "portal_subscriptions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    org_id: Mapped[str] = mapped_column(ForeignKey("portal_organizations.id"), index=True, nullable=False)
    plan_code: Mapped[str] = mapped_column(String(40), default="free", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    price_minor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="UAH", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utcnow, nullable=False)


class Invoice(Base):
    __tablename__ = "portal_invoices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid)
    org_id: Mapped[str] = mapped_column(ForeignKey("portal_organizations.id"), index=True, nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UAH")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="draft")
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utcnow, nullable=False)


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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=utcnow, nullable=False)
