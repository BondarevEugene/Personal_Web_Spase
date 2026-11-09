"""Staged paid subscription tests; use a temporary SQLite database, never Neon."""
from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from server import app
from portal.billing import (
    BillingRuleError, VerifiedPaymentEvidence, add_calendar_months,
    create_pending_invoice, current_entitlements, settle_verified_payment,
)
from portal.billing_admin import configure_plan
from portal.db import engine, session_factory
from portal.models import (BillingPlan, GatewayEvent, Invoice, Organization,
                           PaymentRecord, Subscription, utcnow)


@pytest.fixture()
def billing_db(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'subscription.sqlite3').as_posix()}"
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    engine.cache_clear()
    session_factory.cache_clear()
    cfg = Config(str(Path(__file__).resolve().parent.parent / "portal_alembic.ini"))
    command.upgrade(cfg, "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def org_id(db):
    org = Organization(name="Test Tenant")
    db.add(org)
    db.flush()
    db.add(Subscription(org_id=org.id, plan_code="free", status="active",
                        price_minor=0, currency="UAH"))
    db.flush()
    return org.id


def enabled_plan(db, price=12900):
    configure_plan(db, "start", price, "test-operator", enable=True)


def create_invoice(db, oid, request="my-test-request-123456"):
    return create_pending_invoice(db, oid, "start", request)


def evidence(invoice, event_id="provider_evt_one", external="provider_payment_one", *,
             amount=None, currency=None):
    return VerifiedPaymentEvidence(
        provider="portmone", event_id=event_id, external_payment_id=external,
        invoice_id=invoice.id,
        amount_minor=invoice.amount_minor if amount is None else amount,
        currency=invoice.currency if currency is None else currency,
        verified_at=utcnow())


def test_catalog_starts_free_with_disabled_unpriced_paid_plans(billing_db):
    with session_factory()() as db:
        prices = {p.code: p for p in db.scalars(select(BillingPlan)).all()}
        assert set(prices) == {"free", "start", "growth", "business"}
        assert prices["free"].price_minor == 0 and prices["free"].is_enabled
        assert all(prices[name].price_minor is None and not prices[name].is_enabled
                   for name in ("start", "growth", "business"))
        oid = org_id(db)
        with pytest.raises(BillingRuleError, match="не продаётся"):
            create_invoice(db, oid)


def test_price_snapshot_and_idempotent_invoice(billing_db):
    with session_factory()() as db:
        oid = org_id(db)
        enabled_plan(db)
        invoice = create_invoice(db, oid)
        db.flush()
        assert invoice.amount_minor == 12900 and invoice.status == "pending"
        assert create_invoice(db, oid).id == invoice.id
        assert current_entitlements(db, oid)["paid_access"] is False
        configure_plan(db, "start", 14900, "test-operator")
        assert invoice.amount_minor == 12900
        db.commit()
    with session_factory()() as db:
        invoices = db.scalars(select(Invoice).where(Invoice.org_id == oid)).all()
        assert len(invoices) == 1 and invoices[0].amount_minor == 12900


def test_pending_or_manually_activated_subscription_does_not_grant_access(billing_db):
    with session_factory()() as db:
        oid = org_id(db)
        sub = db.scalar(select(Subscription).where(Subscription.org_id == oid))
        sub.plan_code = "start"
        sub.status = "active"
        sub.current_period_end = utcnow() + timedelta(days=30)
        db.flush()
        rights = current_entitlements(db, oid)
        assert rights["paid_access"] is False
        assert rights["plan"] == "free"


def test_verified_settlement_is_idempotent_and_activates_paid_period(billing_db):
    with session_factory()() as db:
        oid = org_id(db)
        enabled_plan(db)
        invoice = create_invoice(db, oid)
        db.flush()
        payment, newly = settle_verified_payment(db, evidence(invoice))
        assert newly is True
        assert payment.status == "confirmed"
        db.flush()
        assert invoice.status == "paid"
        rights = current_entitlements(db, oid)
        assert rights["paid_access"] is True
        assert rights["plan"] == "start"
        assert rights["online_checkout_enabled"] is False
        same, newly2 = settle_verified_payment(db, evidence(invoice))
        assert same.id == payment.id and newly2 is False
        db.commit()
    with session_factory()() as db:
        assert len(db.scalars(select(PaymentRecord)).all()) == 1
        assert len(db.scalars(select(GatewayEvent)).all()) == 1


def test_replayed_id_for_different_invoice_is_rejected(billing_db):
    with session_factory()() as db:
        oid = org_id(db)
        enabled_plan(db)
        a = create_invoice(db, oid, "first_invoice_123456")
        b = create_invoice(db, oid, "other_invoice_123456")
        db.flush()
        settle_verified_payment(db, evidence(a))
        with pytest.raises(BillingRuleError, match="Conflicting replay"):
            settle_verified_payment(db, evidence(b))


def test_mismatched_payment_is_not_booked_as_revenue(billing_db):
    with session_factory()() as db:
        oid = org_id(db)
        enabled_plan(db)
        invoice = create_invoice(db, oid)
        db.flush()
        with pytest.raises(BillingRuleError, match="amount and currency"):
            settle_verified_payment(db, evidence(invoice, amount=100))
        with pytest.raises(BillingRuleError, match="amount and currency"):
            settle_verified_payment(db, evidence(invoice, currency="USD"))
        assert not db.scalars(select(PaymentRecord)).all()
        assert current_entitlements(db, oid)["paid_access"] is False


def test_month_boundaries_clamped(billing_db):
    from datetime import datetime
    assert add_calendar_months(datetime(2026, 1, 31), 1) == datetime(2026, 2, 28)
    assert add_calendar_months(datetime(2027, 12, 31), 2) == datetime(2028, 2, 29)


def test_billing_public_routes_require_login_and_deny_unpaid_access(billing_db):
    c = TestClient(app)
    assert c.get("/account/billing", follow_redirects=False).status_code == 303
    assert c.get("/account/billing/entitlements").status_code == 401
    assert c.get("/account/billing/paid-access").status_code == 401


def test_registered_user_can_view_catalog_but_cannot_self_unlock(billing_db):
    c = TestClient(app)
    register = c.get("/account/register")
    assert register.status_code == 200
    csrf = c.cookies.get("omni_portal_csrf")
    response = c.post("/account/register", data={
        "csrf_token": csrf, "username": "billing_test", "email": "billing@example.test",
        "display_name": "Billing Test", "organization": "Tenant X",
        "password": "long-testing-password-2026", "password_repeat": "long-testing-password-2026",
    }, follow_redirects=False)
    assert response.status_code == 303, response.text
    r = c.get("/account/billing")
    assert r.status_code == 200
    assert "Start" in r.text
    assert "Стоимость ещё не утверждена" in r.text
    assert c.get("/account/billing/paid-access").status_code == 402
    assert c.get("/account/billing/entitlements").json()["paid_access"] is False
    rejected = c.post("/account/billing/invoices", data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "plan_code": "start", "request_id": "madeup_invoice_request_123456",
    }, follow_redirects=False)
    assert rejected.status_code == 409


def test_invoice_route_owner_scoped_and_requires_signed_csrf(billing_db):
    c = TestClient(app)
    c.get("/account/register")
    c.post("/account/register", data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": "orgtester", "email": "orgtester@example.test",
        "display_name": "Org Tester", "organization": "Org One",
        "password": "long-testing-password-2026", "password_repeat": "long-testing-password-2026",
    }, follow_redirects=False)
    with session_factory()() as db:
        enabled_plan(db)
        db.commit()
    c.get("/account/billing")
    denied = c.post("/account/billing/invoices", data={
        "csrf_token": "forged", "plan_code": "start",
        "request_id": "invoice_request_123456789"
    }, follow_redirects=False)
    assert denied.status_code == 403
    allowed = c.post("/account/billing/invoices", data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "plan_code": "start",
        "request_id": "invoice_request_123456789"
    }, follow_redirects=False)
    assert allowed.status_code == 303, allowed.text
    assert c.get("/account/billing/entitlements").json()["paid_access"] is False
    assert "129.00" in c.get("/account/billing").text
