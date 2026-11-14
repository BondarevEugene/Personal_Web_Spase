"""Subscription accounting domain.

Only a future *verified* payment-provider adapter may call settle_verified_payment.
There is deliberately no customer-controlled HTTP endpoint to mark an invoice
as paid. A pending invoice never unlocks a paid feature.
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from portal.models import (BillingPlan, GatewayEvent, Invoice, Organization,
                           PaymentRecord, Subscription, utcnow)

PAID_PLANS = ("start", "growth", "business")
KNOWN_PROVIDERS = frozenset({"wayforpay", "portmone", "liqpay", "paypal"})
_REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{16,80}$")


class BillingRuleError(ValueError):
    """Business-rule conflict; not a DB or payment-provider error."""


def current_subscription(db: Session, org_id: str, *, locked: bool = False) -> Subscription | None:
    statement = (
        select(Subscription)
        .where(Subscription.org_id == org_id)
        .order_by(Subscription.created_at.desc(), Subscription.id.desc())
        .limit(1)
    )
    if locked:
        statement = statement.with_for_update()
    return db.scalar(statement)


def current_entitlements(db: Session, org_id: str, *, now: datetime | None = None) -> dict:
    now = now or utcnow()
    subscription = current_subscription(db, org_id)
    eligible = (
        subscription is not None
        and subscription.plan_code in PAID_PLANS
        and subscription.status == "active"
        and subscription.current_period_end is not None
        and subscription.current_period_end > now
    )
    if eligible:
        # Do not trust a manually edited subscription.status alone.
        verified_payment = db.scalar(
            select(PaymentRecord.id)
            .join(Invoice, Invoice.id == PaymentRecord.invoice_id)
            .where(Invoice.subscription_id == subscription.id,
                   PaymentRecord.org_id == org_id,
                   PaymentRecord.status == "confirmed",
                   PaymentRecord.verified_at.is_not(None))
            .limit(1)
        )
        eligible = bool(verified_payment)
    return {
        "plan": subscription.plan_code if eligible else "free",
        "paid_access": bool(eligible),
        "subscription_status": (subscription.status if subscription else "free"),
        "paid_until": (subscription.current_period_end.isoformat() if eligible else None),
        "features": {
            "basic_builder_preview": True,
            "local_json_export": True,
            "account_settings": True,
            # The following modules are not implemented, even with a paid plan.
            "server_project_storage": False,
            "managed_bot_deployment": False,
            "crm_sync": False,
        },
        "online_checkout_enabled": False,
        "automatic_recurring_charge_enabled": False,
    }


def create_pending_invoice(db: Session, org_id: str, plan_code: str, request_id: str,
                           *, now: datetime | None = None) -> Invoice:
    """Freeze current catalog price; idempotent per organization/request ID.

    Caller owns the transaction/commit. Pending invoices do not grant access.
    """
    now = now or utcnow()
    if not _REQUEST_ID.fullmatch(request_id):
        raise BillingRuleError("Invalid invoice request identifier")
    if plan_code not in PAID_PLANS:
        raise BillingRuleError("A free plan cannot be invoiced")
    previous = db.scalar(
        select(Invoice)
        .where(Invoice.org_id == org_id, Invoice.idempotency_key == request_id)
    )
    if previous:
        if previous.plan_code != plan_code:
            raise BillingRuleError("Invoice request ID already used for another plan")
        return previous
    plan = db.get(BillingPlan, plan_code)
    if (not plan or not plan.is_public or not plan.is_enabled
            or plan.price_minor is None or plan.price_minor <= 0):
        raise BillingRuleError("Платный тариф пока не продаётся: цена или платёжный канал не настроены.")
    if plan.currency != "UAH" or plan.period_months != 1:
        raise BillingRuleError("Only monthly UAH plan billing is supported in this phase")
    if not db.get(Organization, org_id):
        raise BillingRuleError("Organization does not exist")
    subscription = current_subscription(db, org_id, locked=True)
    if (subscription and subscription.plan_code in PAID_PLANS
            and subscription.status == "active"
            and subscription.current_period_end
            and subscription.current_period_end > now
            and subscription.plan_code != plan_code):
        raise BillingRuleError("Changing an active paid plan requires a separate upgrade workflow")
    invoice = Invoice(
        org_id=org_id, plan_code=plan.code,
        subscription_id=subscription.id if subscription else None,
        period_months=plan.period_months, amount_minor=plan.price_minor,
        currency=plan.currency, status="pending",
        description=f"OmniFactory / {plan.name} / 1 месяц",
        idempotency_key=request_id, due_at=now + timedelta(hours=48),
        created_at=now,
    )
    db.add(invoice)
    db.flush()
    return invoice


def add_calendar_months(value: datetime, count: int) -> datetime:
    """UTC-naive dates, clamp Jan 31 -> Feb 28 for one calendar month."""
    if count < 1 or count > 12:
        raise BillingRuleError("Invalid subscription period")
    index = value.year * 12 + value.month - 1 + count
    year, month_idx = divmod(index, 12)
    month = month_idx + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


@dataclass(frozen=True)
class VerifiedPaymentEvidence:
    """Must be constructed ONLY after checking provider signature/API server-side."""
    provider: Literal["wayforpay", "portmone", "liqpay", "paypal"]
    event_id: str
    external_payment_id: str
    invoice_id: str
    amount_minor: int
    currency: str
    verified_at: datetime


def settle_verified_payment(db: Session, proof: VerifiedPaymentEvidence,
                            *, now: datetime | None = None) -> tuple[PaymentRecord, bool]:
    """Settle an already authenticated event exactly once.

    Returns (record, newly_settled). Caller commits the entire transaction.
    On a concurrent race, the database's unique constraints reject the loser,
    whose adapter should re-fetch the settled record after rollback.
    """
    now = now or utcnow()
    if proof.provider not in KNOWN_PROVIDERS or not 1 <= len(proof.event_id) <= 180:
        raise BillingRuleError("Unrecognized payment provider or event ID")
    if not 1 <= len(proof.external_payment_id) <= 180:
        raise BillingRuleError("Invalid external payment ID")
    if proof.verified_at > now + timedelta(minutes=5):
        raise BillingRuleError("Verification timestamp is in the future")
    old_event = db.scalar(
        select(GatewayEvent)
        .where(GatewayEvent.provider == proof.provider, GatewayEvent.event_id == proof.event_id)
    )
    if old_event:
        payment = db.get(PaymentRecord, old_event.payment_id)
        if (old_event.invoice_id != proof.invoice_id or payment is None
                or payment.external_id != proof.external_payment_id
                or payment.amount_minor != proof.amount_minor
                or payment.currency != proof.currency):
            raise BillingRuleError("Conflicting replay for a verified event ID")
        return payment, False

    invoice = db.scalar(select(Invoice).where(Invoice.id == proof.invoice_id).with_for_update())
    if not invoice or not invoice.plan_code or invoice.plan_code not in PAID_PLANS:
        raise BillingRuleError("Invoice is not a valid subscription invoice")
    if (proof.amount_minor <= 0 or invoice.amount_minor != proof.amount_minor
            or invoice.currency != proof.currency):
        raise BillingRuleError("Verified payment does not match invoice amount and currency")

    previous_payment = db.scalar(
        select(PaymentRecord)
        .where(PaymentRecord.provider == proof.provider,
               PaymentRecord.external_id == proof.external_payment_id)
    )
    if previous_payment:
        if (previous_payment.invoice_id != invoice.id
                or previous_payment.org_id != invoice.org_id
                or previous_payment.amount_minor != proof.amount_minor
                or previous_payment.currency != proof.currency
                or previous_payment.status != "confirmed"):
            raise BillingRuleError("Payment identifier already belongs to another invoice")
        db.add(GatewayEvent(
            provider=proof.provider, event_id=proof.event_id,
            invoice_id=invoice.id, payment_id=previous_payment.id,
            event_type="payment.confirmed", verified_at=proof.verified_at,
        ))
        db.flush()
        return previous_payment, False
    if invoice.status != "pending":
        raise BillingRuleError("Invoice is not awaiting payment")
    if invoice.due_at and invoice.due_at < now:
        raise BillingRuleError("Invoice expired; provider event requires manual reconciliation")
    subscription = current_subscription(db, invoice.org_id, locked=True)
    if (subscription and subscription.plan_code in PAID_PLANS
            and subscription.status == "active" and subscription.current_period_end
            and subscription.current_period_end > now and subscription.plan_code != invoice.plan_code):
        raise BillingRuleError("An active subscription cannot be switched automatically")

    record = PaymentRecord(
        org_id=invoice.org_id, invoice_id=invoice.id,
        provider=proof.provider, external_id=proof.external_payment_id,
        amount_minor=proof.amount_minor, currency=proof.currency,
        status="confirmed", verified_at=proof.verified_at, created_at=now,
    )
    db.add(record)
    db.flush()
    if subscription is None:
        subscription = Subscription(org_id=invoice.org_id)
        db.add(subscription)
        db.flush()
    start = now
    if (subscription.plan_code == invoice.plan_code
            and subscription.current_period_end
            and subscription.current_period_end > now
            and not subscription.cancel_at_period_end):
        start = subscription.current_period_end
    subscription.plan_code = invoice.plan_code
    subscription.status = "active"
    subscription.price_minor = invoice.amount_minor
    subscription.currency = invoice.currency
    subscription.current_period_start = start
    subscription.current_period_end = add_calendar_months(start, invoice.period_months)
    subscription.cancel_at_period_end = False
    invoice.subscription_id = subscription.id
    invoice.status = "paid"
    invoice.paid_at = now
    db.add(GatewayEvent(
        provider=proof.provider, event_id=proof.event_id,
        invoice_id=invoice.id, payment_id=record.id,
        event_type="payment.confirmed", verified_at=proof.verified_at,
    ))
    db.flush()
    return record, True
