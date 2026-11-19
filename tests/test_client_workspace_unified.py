"""Unified Client Workspace: navigation, live priorities, and tenant isolation."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from portal.db import engine, session_factory
from portal.models import ClientProject, Customer, Organization, utcnow
from server import app

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "dashboard.html", "client_projects.html", "client_project_detail.html",
    "client_notifications.html", "client_finance.html", "billing.html",
    "tickets.html", "ticket_detail.html",
]


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "unified_workspace.sqlite3").as_posix()
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
        "username": name, "display_name": name.title(),
        "organization": name + " org", "email": name + "@workspace.test",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    })
    assert response.status_code == 303, response.text
    return client


def test_shared_navigation_links_only_to_existing_real_routes():
    shell = (ROOT / "portal" / "templates" / "_workspace_nav.html").read_text(
        encoding="utf-8"
    )
    expected = ["/account", "/account/projects", "/account/notifications",
                "/account/tickets", "/account/finance", "/account/billing",
                "/architect", "/automation/studio"]
    for target in expected:
        assert 'href="' + target + '"' in shell
    for filename in PAGES:
        text = (ROOT / "portal" / "templates" / filename).read_text(
            encoding="utf-8"
        )
        assert '{% include "_workspace_nav.html" %}' in text, filename
        assert 'client_workspace.css?v=1' in text, filename
    assert 'aria-current="page"' in shell


def test_real_dashboard_attention_counters_are_org_scoped(db_ready):
    customer = register("workspaceowner")
    other = register("workspaceother")
    with session_factory()() as db:
        owner = db.scalar(select(Customer).where(
            Customer.username == "workspaceowner"))
        outsider = db.scalar(select(Customer).where(
            Customer.username == "workspaceother"))
        assert owner.org_id != outsider.org_id
        db.add_all([
            ClientProject(org_id=owner.org_id, created_by_id=owner.id,
                          title="Review for customer", brief="Valid review project text",
                          status="review"),
            ClientProject(org_id=owner.org_id, created_by_id=owner.id,
                          title="Overdue build", brief="Valid overdue project text",
                          status="in_progress", due_date=utcnow() - timedelta(days=2)),
            ClientProject(org_id=outsider.org_id, created_by_id=outsider.id,
                          title="Other private review", brief="Should remain private",
                          status="review"),
        ])
        db.commit()
    response = customer.get("/account")
    assert response.status_code == 200, response.text
    assert "Review for customer" in response.text
    assert "Other private review" not in response.text
    assert 'aria-label="Требует внимания"' in response.text
    assert "<strong>1</strong><span>Проектов на приёмке</span>" in response.text
    assert "<strong>1</strong><span>Проектов с истёкшим сроком</span>" in response.text
    assert 'aria-current="page"' in response.text
    assert "Рабочий кабинет" in response.text
    other_page = other.get("/account")
    assert other_page.status_code == 200
    assert "Review for customer" not in other_page.text
    assert "<strong>1</strong><span>Проектов на приёмке</span>" in other_page.text
    assert "<strong>0</strong><span>Проектов с истёкшим сроком</span>" in other_page.text


def test_client_subpages_render_consistent_shell(db_ready):
    client = register("workspacetabs")
    for path in ("/account", "/account/projects", "/account/notifications",
                 "/account/tickets", "/account/finance?period=2026-11",
                 "/account/billing"):
        response = client.get(path)
        assert response.status_code == 200, (path, response.text[:500])
        assert 'class="workspace-nav"' in response.text, path
        assert "Graph Studio" in response.text
        assert "Финансы" in response.text
