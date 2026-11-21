"""End-to-end UA/RU/EN locale persistence across authenticated client pages."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from portal.db import engine, session_factory
from portal.i18n import LANGUAGES, normalize_language, translator
from portal.models import Customer, CustomerSettings
from server import app

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "/account", "/account/projects", "/account/notifications",
    "/account/finance?period=2026-11", "/account/billing", "/account/tickets",
]


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "client_i18n.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    engine.cache_clear()
    session_factory.cache_clear()
    command.upgrade(Config(str(ROOT / "portal_alembic.ini")), "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register(name: str):
    client = TestClient(app)
    assert client.get("/account/register").status_code == 200
    response = client.post("/account/register", follow_redirects=False, data={
        "csrf_token": client.cookies.get("omni_portal_csrf"),
        "username": name,
        "display_name": name,
        "email": name + "@locale.test",
        "organization": name + " organization",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    })
    assert response.status_code == 303, response.text
    return client


def test_locale_normalization_and_explicit_translations():
    assert LANGUAGES == ("uk", "ru", "en")
    for invalid in (None, "de", "UA", "", [], {"uk": True}):
        assert normalize_language(invalid) == "ru"
    assert translator("uk")("Заказы") == "Замовлення"
    assert translator("en")("Заказы") == "Orders"
    assert translator("ru")("Заказы") == "Заказы"
    assert translator("en")("Принят клиентом") == "Accepted by client"
    assert translator("uk")("Согласовано") == "Погоджено"
    assert translator("en")("unknown business field") == "unknown business field"


def test_workspace_language_is_real_db_setting_and_persists_across_pages(db_ready):
    client = register("localowner")
    secondary = register("localother")
    assert 'lang="ru"' in client.get("/account").text
    assert 'aria-pressed="true">RU</button>' in client.get("/account").text

    # CSRF must protect the language-setting endpoint.
    forbidden = client.post("/account/language", data={"language": "en"})
    assert forbidden.status_code == 403
    assert client.post("/account/language", data={
        "csrf_token": client.cookies.get("omni_portal_csrf"),
        "language": "fr",
    }).status_code == 422

    for language, translated_nav in [
        ("uk", "Замовлення"), ("en", "Orders"), ("ru", "Заказы")
    ]:
        updated = client.post("/account/language", data={
            "csrf_token": client.cookies.get("omni_portal_csrf"),
            "language": language,
        }, follow_redirects=False)
        assert updated.status_code == 303, updated.text
        for path in PAGES:
            response = client.get(path)
            assert response.status_code == 200, (path, response.text[:500])
            assert 'lang="' + language + '"' in response.text
            assert translated_nav in response.text
            assert 'name="language" value="' + language + '"' in response.text
        with session_factory()() as db:
            customer = db.scalar(select(Customer).where(
                Customer.username == "localowner"
            ))
            settings = db.get(CustomerSettings, customer.id)
            assert settings.language == language

    assert 'lang="ru"' in secondary.get("/account").text
    assert "Orders" not in secondary.get("/account").text


def test_workspace_templates_have_only_server_rendered_locale_switch():
    shared = (ROOT / "portal/templates/_workspace_nav.html").read_text(
        encoding="utf-8"
    )
    assert 'action="/account/language"' in shared
    assert 'name="csrf_token"' in shared
    for name in (
        "dashboard.html", "client_projects.html", "client_project_detail.html",
        "client_finance.html", "client_notifications.html", "billing.html",
        "tickets.html", "ticket_detail.html",
    ):
        body = (ROOT / "portal/templates" / name).read_text(encoding="utf-8")
        assert '<html lang="{{ ui_lang }}">' in body, name
        assert 'client_workspace.css?v=2' in body, name
        assert '{% include "_workspace_nav.html" %}' in body, name
        assert "{{ t(" in body, name
    # Business amounts, access checks and document version IDs remain server data.
    billing = (ROOT / "portal/templates/client_finance.html").read_text(
        encoding="utf-8"
    )
    assert 'format(amount.confirmed / 100)' in billing
