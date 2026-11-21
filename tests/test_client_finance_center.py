"""Finance center: verified-only accounting, CSV safety and tenant boundaries."""
from datetime import datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select

from portal.db import engine, session_factory
from portal.finance_center import excel_safe, month_bounds, statement
from portal.models import Invoice, Organization, PaymentRecord
from server import app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "finance_center.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    engine.cache_clear()
    session_factory.cache_clear()
    command.upgrade(Config(str(ROOT / "portal_alembic.ini")), "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register(username):
    c = TestClient(app)
    c.get("/account/register")
    r = c.post("/account/register", data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": username, "email": username + "@finance.test",
        "display_name": username,
        "organization": username + " org",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    }, follow_redirects=False)
    assert r.status_code == 303, r.text
    return c


def test_period_validation_and_csv_formula_escaping():
    assert month_bounds("2026-11")[0] == "2026-11"
    assert month_bounds("2026-12")[2] == datetime(2027, 1, 1)
    for raw in ("2026-13", "2026-00", "2026-1", "0000-01", "2101-01", "invalid"):
        with pytest.raises(HTTPException) as e:
            month_bounds(raw)
        assert e.value.status_code == 422
    assert excel_safe("=1+2") == "'=1+2"
    assert excel_safe("+SUM(A1)") == "'+SUM(A1)"
    assert excel_safe("@run") == "'@run"
    assert excel_safe("ordinary") == "ordinary"


def test_client_statement_separates_pending_and_verified_payments(db_ready):
    owner = register("financemain")
    other = register("financeother")
    with session_factory()() as db:
        owner_org = db.scalar(select(Organization.id).where(
            Organization.name == "financemain org"
        ))
        other_org = db.scalar(select(Organization.id).where(
            Organization.name == "financeother org"
        ))
        invoice = Invoice(
            org_id=owner_org, amount_minor=12345, currency="UAH",
            status="pending", description="=Potential spreadsheet formula",
            created_at=datetime(2026, 11, 10),
        )
        paid_invoice = Invoice(
            org_id=owner_org, amount_minor=5000, currency="UAH",
            status="paid", description="Paid invoice",
            created_at=datetime(2026, 11, 8),
        )
        db.add_all([invoice, paid_invoice])
        db.flush()
        db.add_all([
            PaymentRecord(
                org_id=owner_org, invoice_id=paid_invoice.id,
                provider="wayforpay", external_id="evidence-verified-1",
                amount_minor=5000, currency="UAH", status="confirmed",
                verified_at=datetime(2026, 11, 9),
                created_at=datetime(2026, 11, 9),
            ),
            # A forged/incomplete record must never count toward confirmed.
            PaymentRecord(
                org_id=owner_org, invoice_id=invoice.id,
                provider="wayforpay", external_id="evidence-unverified-2",
                amount_minor=9999, currency="UAH", status="confirmed",
                verified_at=None, created_at=datetime(2026, 11, 10),
            ),
        ])
        db.commit()
        _, start, end = month_bounds("2026-11")
        invoices, payments, totals = statement(db, owner_org, start, end)
        assert len(invoices) == 2
        assert len(payments) == 1
        assert totals == {"UAH": {
            "invoiced": 17345, "pending": 12345, "confirmed": 5000,
        }}
        _, other_payments, other_totals = statement(db, other_org, start, end)
        assert other_payments == []
        assert other_totals == {}

    page = owner.get("/account/finance?period=2026-11")
    assert page.status_code == 200, page.text
    assert "123.45" in page.text
    assert "50.00" in page.text
    assert "=Potential spreadsheet formula" in page.text
    assert "=Potential spreadsheet formula" not in other.get(
        "/account/finance?period=2026-11"
    ).text

    exported = owner.get("/account/finance/export.csv?period=2026-11")
    assert exported.status_code == 200
    assert "text/csv" in exported.headers["content-type"]
    assert "no-store" in exported.headers["cache-control"]
    assert "'=Potential spreadsheet formula" in exported.text
    assert "evidence-unverified-2" not in exported.text
    assert other.get("/account/finance/export.csv?period=2026-11").status_code == 200
    assert "Paid invoice" not in other.get(
        "/account/finance/export.csv?period=2026-11"
    ).text


def test_finance_requires_login_and_does_not_offer_payment_mutations(db_ready):
    anonymous = TestClient(app)
    assert anonymous.get("/account/finance", follow_redirects=False).status_code == 303
    assert anonymous.get("/account/finance/export.csv").status_code == 401
    paths = {(route.path, method) for route in app.routes
             for method in getattr(route, "methods", set())}
    assert ("/account/finance", "GET") in paths
    assert ("/account/finance/export.csv", "GET") in paths
    assert ("/account/finance", "POST") not in paths
    assert ("/account/finance/export.csv", "POST") not in paths
