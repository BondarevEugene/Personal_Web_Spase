"""Real account security acceptance: password rotation and session revocation."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from portal.db import engine, session_factory
from portal.models import Customer, PortalSession
from portal.security import password_matches
from server import app

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = "Strong-Password-2026"
UPDATED = "New-Strong-Password-2026"


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "account_security.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    engine.cache_clear()
    session_factory.cache_clear()
    command.upgrade(Config(str(ROOT / "portal_alembic.ini")), "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register(name):
    client = TestClient(app)
    assert client.get("/account/register").status_code == 200
    response = client.post("/account/register", follow_redirects=False, data={
        "csrf_token": client.cookies.get("omni_portal_csrf"),
        "username": name, "email": name + "@security.test",
        "display_name": name.title(),
        "organization": name + " organization",
        "password": ORIGINAL,
        "password_repeat": ORIGINAL,
    })
    assert response.status_code == 303, response.text
    return client


def login(name, password):
    client = TestClient(app)
    assert client.get("/account/login").status_code == 200
    result = client.post("/account/login", follow_redirects=False, data={
        "csrf_token": client.cookies.get("omni_portal_csrf"),
        "login": name, "password": password,
    })
    assert result.status_code == 303, result.text
    return client


def csrf(client, path="/account/security"):
    response = client.get(path)
    assert response.status_code == 200, response.text[:500]
    return client.cookies.get("omni_portal_csrf")


def test_password_change_rotates_token_and_revokes_all_old_devices(db_ready):
    original = register("securityowner")
    second = login("securityowner", ORIGINAL)
    other_org = register("securityother")
    first_cookie = original.cookies.get("omni_portal_session")
    second_cookie = second.cookies.get("omni_portal_session")
    assert first_cookie and second_cookie and first_cookie != second_cookie

    assert "Сеансы входа" in original.get("/account/security").text
    assert original.post("/account/security/password", data={
        "current_password": ORIGINAL, "new_password": UPDATED,
        "repeat_password": UPDATED,
    }).status_code == 403
    assert original.post("/account/security/password", data={
        "csrf_token": csrf(original),
        "current_password": "incorrect", "new_password": UPDATED,
        "repeat_password": UPDATED,
    }).status_code == 403
    assert original.post("/account/security/password", data={
        "csrf_token": csrf(original),
        "current_password": ORIGINAL, "new_password": UPDATED,
        "repeat_password": "not matching",
    }).status_code == 422

    changed = original.post("/account/security/password", follow_redirects=False,
                            data={
        "csrf_token": csrf(original),
        "current_password": ORIGINAL, "new_password": UPDATED,
        "repeat_password": UPDATED,
    })
    assert changed.status_code == 303, changed.text
    assert changed.headers["location"].startswith("/account/security")
    assert first_cookie != original.cookies.get("omni_portal_session")
    assert original.get("/account/security").status_code == 200
    assert second.get("/account", follow_redirects=False).status_code == 303
    assert other_org.get("/account").status_code == 200

    with session_factory()() as db:
        user = db.scalar(select(Customer).where(Customer.username == "securityowner"))
        assert password_matches(user.password_hash, UPDATED)
        assert not password_matches(user.password_hash, ORIGINAL)
        sessions = db.scalars(select(PortalSession).where(
            PortalSession.customer_id == user.id,
        )).all()
        assert len(sessions) == 1
    assert login("securityowner", UPDATED).get("/account").status_code == 200


def test_logout_other_sessions_retains_current_login(db_ready):
    first = register("sessionowner")
    second = login("sessionowner", ORIGINAL)
    other_org = register("sessionother")
    request = first.post("/account/security/revoke-others", follow_redirects=False, data={
        "csrf_token": csrf(first), "password": ORIGINAL,
    })
    assert request.status_code == 303
    assert first.get("/account").status_code == 200
    assert second.get("/account", follow_redirects=False).status_code == 303
    assert other_org.get("/account").status_code == 200

    third = login("sessionowner", ORIGINAL)
    assert third.post("/account/security/logout-all", data={
        "csrf_token": csrf(third), "password": "incorrect",
    }).status_code == 403
    gone = third.post("/account/security/logout-all", follow_redirects=False, data={
        "csrf_token": csrf(third), "password": ORIGINAL,
    })
    assert gone.status_code == 303
    assert third.get("/account", follow_redirects=False).status_code == 303
    assert first.get("/account", follow_redirects=False).status_code == 303
    assert other_org.get("/account").status_code == 200


def test_security_page_is_localized_and_requires_login(db_ready):
    customer = register("securelocale")
    anonymous = TestClient(app)
    assert anonymous.get("/account/security", follow_redirects=False).status_code == 303
    for lang, expected in (
        ("uk", "Безпека облікового запису"),
        ("en", "Account security"),
        ("ru", "Безопасность аккаунта"),
    ):
        result = customer.post("/account/language", follow_redirects=False, data={
            "csrf_token": csrf(customer), "language": lang,
        })
        assert result.status_code == 303
        page = customer.get("/account/security")
        assert page.status_code == 200
        assert 'lang="' + lang + '"' in page.text
        assert expected in page.text
        assert 'action="/account/security/password"' in page.text
        assert 'action="/account/security/logout-all"' in page.text


def test_no_secrets_or_session_tokens_rendered(db_ready):
    client = register("secretviewer")
    page = client.get("/account/security")
    assert page.status_code == 200
    assert ORIGINAL not in page.text
    assert client.cookies.get("omni_portal_session") not in page.text
    assert "token_hash" not in page.text
    assert 'name="csrf_token"' in page.text
