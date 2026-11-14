"""Customer portal integration tests: no Neon credentials or external calls required."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from server import app
from portal.db import engine, session_factory
from portal.models import Customer, Invoice, Organization, PortalSession, RegistrationEvent, Subscription
from portal.security import SESSION_COOKIE, token_hash
from portal.report import summarize


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'customer_portal.sqlite3').as_posix()}"
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


def csrf(client):
    r = client.get("/account/register")
    assert r.status_code == 200, r.text
    assert "/studio-assets/site.css" in r.text
    return client.cookies.get("omni_portal_csrf")


def register(client, username="sample_user", email="sample@example.test", organization="Company One"):
    token = csrf(client)
    return client.post("/account/register", data={
        "csrf_token": token, "username": username, "email": email,
        "display_name": "Test Client", "organization": organization,
        "password": "Long-Test-Password-2026", "password_repeat": "Long-Test-Password-2026"
    }, follow_redirects=False)


def test_registration_session_and_company_are_recorded(db_ready):
    client = TestClient(app)
    result = register(client)
    assert result.status_code == 303, result.text
    assert result.headers["location"] == "/account"
    session_cookie = client.cookies.get(SESSION_COOKIE)
    assert session_cookie and len(session_cookie) > 32
    r = client.get("/account")
    assert r.status_code == 200
    assert "Company One" in r.text
    assert "sample_user" in r.text
    with session_factory()() as db:
        user = db.scalar(select(Customer).where(Customer.email == "sample@example.test"))
        assert user
        assert user.password_hash != "Long-Test-Password-2026"
        assert user.password_hash.startswith("$argon2id$")
        assert user.email_verified is False
        assert db.get(PortalSession, token_hash(session_cookie))
        assert len(db.scalars(select(RegistrationEvent)).all()) == 1
        subscription = db.scalar(select(Subscription).where(Subscription.org_id == user.org_id))
        assert subscription.plan_code == "free"
        assert subscription.price_minor == 0


def test_invalid_csrf_is_rejected(db_ready):
    client = TestClient(app)
    csrf(client)
    r = client.post("/account/register", data={"csrf_token": "attacker", "username": "aaaa"})
    assert r.status_code == 403


def test_duplicate_registration_does_not_create_second_company(db_ready):
    c1 = TestClient(app)
    assert register(c1).status_code == 303
    c2 = TestClient(app)
    r = register(c2, email="other@example.test")
    assert r.status_code == 200
    assert "уже используется" in r.text
    with session_factory()() as db:
        assert len(db.scalars(select(Organization)).all()) == 1


def test_login_with_username_and_logout_revokes_server_session(db_ready):
    first = TestClient(app)
    assert register(first).status_code == 303
    client = TestClient(app)
    form = client.get("/account/login")
    assert form.status_code == 200
    token = client.cookies.get("omni_portal_csrf")
    bad = client.post("/account/login", data={"csrf_token": token,
                      "login": "sample_user", "password": "incorrect"}, follow_redirects=False)
    assert bad.status_code == 200
    ok = client.post("/account/login", data={"csrf_token": client.cookies.get("omni_portal_csrf"),
                     "login": "sample_user", "password": "Long-Test-Password-2026"}, follow_redirects=False)
    assert ok.status_code == 303
    assert client.get("/account").status_code == 200
    cookie = client.cookies.get(SESSION_COOKIE)
    form_token = client.cookies.get("omni_portal_csrf")
    logout = client.post("/account/logout", data={"csrf_token": form_token}, follow_redirects=False)
    assert logout.status_code == 303
    with session_factory()() as db:
        assert db.get(PortalSession, token_hash(cookie)) is None
    assert client.get("/account", follow_redirects=False).status_code == 303


def test_settings_are_personal_and_csrf_protected(db_ready):
    client = TestClient(app)
    assert register(client).status_code == 303
    r = client.get("/account")
    assert r.status_code == 200
    token = client.cookies.get("omni_portal_csrf")
    invalid = client.post("/account/settings", data={
        "csrf_token": "bad", "display_name": "Another", "language": "uk",
        "timezone": "Europe/Kyiv"}, follow_redirects=False)
    assert invalid.status_code == 403
    updated = client.post("/account/settings", data={
        "csrf_token": token, "display_name": "New Display Name",
        "language": "uk", "timezone": "Europe/Kyiv", "marketing_opt_in": "yes",
    }, follow_redirects=False)
    assert updated.status_code == 303
    assert "New Display Name" in client.get("/account").text


def test_organizations_cannot_read_each_others_invoices(db_ready):
    a, b = TestClient(app), TestClient(app)
    assert register(a, username="org_first", email="first@example.test",
                    organization="First company").status_code == 303
    assert register(b, username="org_second", email="second@example.test",
                    organization="Second company").status_code == 303
    with session_factory()() as db:
        users = {u.username: u for u in db.scalars(select(Customer)).all()}
        db.add(Invoice(org_id=users["org_first"].org_id, amount_minor=12500,
                       currency="UAH", status="draft", description="Private Invoice A"))
        db.add(Invoice(org_id=users["org_second"].org_id, amount_minor=9000,
                       currency="UAH", status="draft", description="Private Invoice B"))
        db.commit()
    one = a.get("/account").text
    two = b.get("/account").text
    assert "Private Invoice A" in one and "Private Invoice B" not in one
    assert "Private Invoice B" in two and "Private Invoice A" not in two


def test_private_account_redirects_unauthenticated(db_ready):
    client = TestClient(app)
    r = client.get("/account", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/account/login"
    post = client.post("/account/settings", data={"display_name": "Hacker"})
    assert post.status_code == 403


def test_registration_accounting_is_not_fake_revenue(db_ready):
    a, b = TestClient(app), TestClient(app)
    assert register(a, username="accounting_a", email="accountinga@example.test").status_code == 303
    assert register(b, username="accounting_b", email="accountingb@example.test").status_code == 303
    with session_factory()() as db:
        summary = summarize(db)
    assert summary["registration_events"] == 2
    assert summary["organizations"] == 2
    assert summary["customers"] == 2
    assert summary["confirmed_revenue_by_currency_minor"] == {}
    assert summary["payment_gateway_connected"] is False
    assert summary["subscriptions_by_plan"] == {"free": 2}

def test_portal_build_fingerprint(db_ready):
    client = TestClient(app)
    response = client.get("/")
    assert response.headers.get("x-omni-ui") == "studio-v3-platform"
    assert response.headers.get("cache-control", "").startswith("no-store")
    health = client.get("/health").json()
    assert health["platform_ui"] == "studio-v3-platform"
    assert health["customer_portal"] == "accounts-v1"


def test_forged_csrf_cannot_be_accepted_even_with_matching_cookie(db_ready):
    client = TestClient(app)
    client.get("/account/register")
    forged = "chosen-by-attacker.forged-signature"
    client.cookies.set("omni_portal_csrf", forged)
    response = client.post("/account/register", data={"csrf_token": forged, "username": "hacker"})
    assert response.status_code == 403


def test_eight_character_password_is_accepted(db_ready):
    client = TestClient(app)
    token = csrf(client)
    result = client.post("/account/register", data={
        "csrf_token": token,
        "username": "shortpass",
        "email": "short-pass@example.test",
        "display_name": "Test Customer",
        "organization": "Company Alpha",
        "password": "safe8Pwd",
        "password_repeat": "safe8Pwd",
    }, follow_redirects=False)
    assert result.status_code == 303
    assert client.get("/account").status_code == 200


def test_seven_character_password_is_rejected(db_ready):
    client = TestClient(app)
    token = csrf(client)
    response = client.post("/account/register", data={
        "csrf_token": token,
        "username": "weakpass",
        "email": "weak-pass@example.test",
        "display_name": "Test Customer",
        "organization": "Company Alpha",
        "password": "1234567",
        "password_repeat": "1234567",
    }, follow_redirects=False)
    assert response.status_code == 200
    assert "от 8 символов" in response.text
    with session_factory()() as db:
        assert db.scalar(select(Customer).where(Customer.username == "weakpass")) is None
