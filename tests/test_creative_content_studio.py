"""End-to-end Creative Studio publication and independent brand copy safety."""
from datetime import timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from omni_site.case_library import CASES
from omni_site.creative_store import (
    HOME_HERO, catalog, read_override, render_home_hero, utcnow,
    validate_copy,
)
from omni_site.services_catalog import SERVICES
from portal.db import engine, session_factory
from portal.models import Customer, PublicPageRevision
from server import app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "creative_studio.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    monkeypatch.delenv("OMNI_SUPPORT_OPERATOR_IDS", raising=False)
    engine.cache_clear()
    session_factory.cache_clear()
    command.upgrade(Config(str(ROOT / "portal_alembic.ini")), "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def registered(name):
    client = TestClient(app)
    assert client.get("/account/register").status_code == 200
    result = client.post("/account/register", follow_redirects=False, data={
        "csrf_token": client.cookies.get("omni_portal_csrf"),
        "username": name, "display_name": name.title(),
        "email": name + "@creative.test", "organization": name + " studio",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    })
    assert result.status_code == 303, result.text
    return client


def csrf(client, url):
    response = client.get(url)
    assert response.status_code == 200, response.text[:500]
    return client.cookies.get("omni_portal_csrf")


def operator(monkeypatch):
    client = registered("creativeowner")
    with session_factory()() as db:
        user = db.scalar(select(Customer).where(
            Customer.username == "creativeowner"
        ))
        monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", user.id)
    return client


def test_admin_requires_allowlisted_operator(db_ready, monkeypatch):
    ordinary = registered("creativevisitor")
    assert ordinary.get("/support/creative").status_code == 403
    assert ordinary.get("/support/creative/service/custom-crm").status_code == 403
    assert TestClient(app).get("/support/creative").status_code == 401
    with session_factory()() as db:
        customer = db.scalar(select(Customer).where(
            Customer.username == "creativevisitor"
        ))
    monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", customer.id)
    page = ordinary.get("/support/creative")
    assert page.status_code == 200
    assert "CONTENT STUDIO" in page.text
    assert 'href="/support/creative/home/hero"' in page.text
    assert len(catalog()) == len(CASES) + len(SERVICES) + 1


def test_service_copy_draft_publish_and_source_rollback(db_ready, monkeypatch):
    client = operator(monkeypatch)
    original = SERVICES[0]
    path = "/support/creative/service/" + original.slug
    public = "/services/" + original.slug
    title = "Выразительная CRM для ваших бизнес-процессов"
    summary = "Клиентский кабинет и прозрачные процессы с понятными этапами, документами и историей решений."
    assert title not in client.get(public).text
    assert client.post(path + "/save", data={
        "title": title, "summary": summary,
    }).status_code == 403
    response = client.post(path + "/save", follow_redirects=False, data={
        "csrf_token": csrf(client, path),
        "title": title, "summary": summary,
    })
    assert response.status_code == 303
    assert title not in client.get(public).text
    assert title in client.get(path).text
    published = client.post(path + "/publish", follow_redirects=False, data={
        "csrf_token": csrf(client, path),
    })
    assert published.status_code == 303
    assert title in client.get(public).text
    assert title in client.get("/services").text
    assert original.case_url in client.get(public).text
    assert original.journal_url in client.get(public).text
    rollback = client.post(path + "/restore", follow_redirects=False, data={
        "csrf_token": csrf(client, path),
    })
    assert rollback.status_code == 303
    assert original.title in client.get(public).text
    assert title not in client.get(public).text


def test_scheduled_copy_preserves_live_until_due(db_ready, monkeypatch):
    client = operator(monkeypatch)
    item = CASES[0]
    path = "/support/creative/case/" + item.slug
    public = "/cases/" + item.slug
    original = client.get(public)
    assert original.status_code == 200
    title = "Новая графическая подача визуального конструктора"
    summary = "Проверяемая архитектура графа, переходы, переменные и экспорт Python без фиктивных обещаний."
    assert client.post(path + "/save", follow_redirects=False, data={
        "csrf_token": csrf(client, path),
        "title": title, "summary": summary,
    }).status_code == 303

    future = utcnow() + timedelta(days=3)
    scheduled = client.post(path + "/publish", follow_redirects=False, data={
        "csrf_token": csrf(client, path),
        "scheduled_at": future.strftime("%Y-%m-%dT%H:%M"),
    })
    assert scheduled.status_code == 303
    assert title not in client.get(public).text
    with session_factory()() as db:
        row = db.get(PublicPageRevision, "case:" + item.slug)
        assert row.scheduled_title == title
        assert row.published_title is None

    monkeypatch.setattr(
        "omni_site.creative_store.utcnow",
        lambda: future + timedelta(minutes=2),
    )
    assert title in client.get(public).text
    assert title in client.get("/cases").text
    assert item.source_url in client.get(public).text


def test_homepage_copy_is_escaped_and_preserves_builder_links(db_ready, monkeypatch):
    client = operator(monkeypatch)
    path = "/support/creative/home/hero"
    headline = "Наш процесс | <script>alert(1)</script> под контролем"
    summary = (
        "Сценарии Telegram, кабинеты и прозрачные системы для бизнеса "
        "с проверяемыми этапами и оригинальными исходными проектами."
    )
    assert client.post(path + "/save", follow_redirects=False, data={
        "csrf_token": csrf(client, path),
        "title": headline, "summary": summary,
    }).status_code == 303
    assert client.post(path + "/publish", follow_redirects=False, data={
        "csrf_token": csrf(client, path),
    }).status_code == 303
    html = client.get("/").text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert '<span class="gradient-text">' in html
    assert 'href="/architect"' in html
    assert 'href="/studio#contact"' in html
    assert "id=\"growth-calculator\"" in html
    assert client.post(path + "/restore", follow_redirects=False, data={
        "csrf_token": csrf(client, path),
    }).status_code == 303
    assert HOME_HERO.title.split("|")[0].strip() in client.get("/").text


def test_guarded_copy_and_exact_hero_markup():
    with pytest.raises(ValueError):
        validate_copy("short", "Valid copy " * 10)
    with pytest.raises(ValueError):
        validate_copy("Long enough headline", "too short")
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    assert render_home_hero(source, None) == source
    assert render_home_hero("unrelated page", ("Very long title", "A" * 60)) == (
        "unrelated page"
    )


def test_unknown_slug_is_never_editable(db_ready, monkeypatch):
    client = operator(monkeypatch)
    assert client.get("/support/creative/case/made-up").status_code == 404
    assert client.post("/support/creative/service/made-up/save", data={
        "csrf_token": csrf(client, "/support/creative"),
        "title": "Long enough headline", "summary": "A" * 70,
    }).status_code == 404
    assert read_override(session_factory()(), "unknown:slug") is None
