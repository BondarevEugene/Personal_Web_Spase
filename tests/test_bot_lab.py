"""Bot Lab authentic inventory and Railway read-only API contract."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from automation import railway_oauth
from automation.railway_inventory import RailwayReadError, list_projects
from portal.db import engine, session_factory
from portal.models import CloudOAuthConnection, utcnow
from server import app

BASE = "/api/v1/bot-lab"


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "bot_lab.sqlite3").as_posix()
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", url)
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", url)
    monkeypatch.setenv("OMNI_CLOUD_OAUTH_FERNET_KEY", Fernet.generate_key().decode())
    engine.cache_clear()
    session_factory.cache_clear()
    config = Config(str(Path(__file__).resolve().parents[1] / "portal_alembic.ini"))
    command.upgrade(config, "head")
    yield
    engine().dispose()
    engine.cache_clear()
    session_factory.cache_clear()


def register(username):
    c = TestClient(app)
    assert c.get("/account/register").status_code == 200
    result = c.post("/account/register", data={
        "csrf_token": c.cookies.get("omni_portal_csrf"),
        "username": username, "email": username + "@test.example",
        "display_name": "Bot Lab Tester", "organization": username + " company",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    }, follow_redirects=False)
    assert result.status_code == 303, result.text
    return c


def csrf(c):
    res = c.get("/api/v1/builder/projects/csrf")
    assert res.status_code == 200
    return {"X-Omni-CSRF": res.json()["csrf_token"]}


def test_lab_page_requires_login_and_old_admin_redirects(db_ready):
    guest = TestClient(app)
    assert guest.get("/bots/lab", follow_redirects=False).headers["location"] == "/account/login"
    assert guest.get("/bot-lab", follow_redirects=False).status_code == 303
    assert guest.get("/admin", follow_redirects=False).headers["location"] == "/bots/lab"
    assert guest.get("/admin/", follow_redirects=False).headers["location"] == "/bots/lab"
    assert guest.get("/admin/dashboard", follow_redirects=False).headers["location"] == "/bots/lab"
    assert guest.get(BASE + "/overview").status_code == 401
    assert guest.get(BASE + "/railway/projects").status_code == 401
    c = register("lab_authorized")
    response = c.get("/bots/lab")
    assert response.status_code == 200
    assert "id=\"lab-bots-list\"" in response.text
    assert response.headers.get("cache-control") == "no-store"


def test_lab_lists_only_owner_data_and_no_mock_metrics(db_ready):
    owner = register("lab_owner")
    other = register("lab_other")
    create = owner.post("/api/v1/builder/projects", headers=csrf(owner),
                        json={"scenario": {
                            "name": "My Telegram Bot", "start": "start",
                            "nodes": [{"id": "start", "kind": "message",
                                       "text": "Welcome", "next": "finish"},
                                      {"id": "finish", "kind": "end", "text": "Bye"}]}})
    assert create.status_code == 201, create.text
    data = owner.get(BASE + "/overview")
    assert data.status_code == 200, data.text
    assert len(data.json()["bot_projects"]) == 1
    assert data.json()["bot_projects"][0]["name"] == "My Telegram Bot"
    assert data.json()["bot_projects"][0]["status"] == "draft"
    assert data.json()["capabilities"]["real_deployment"] is False
    outsider = other.get(BASE + "/overview")
    assert outsider.status_code == 200
    assert outsider.json()["bot_projects"] == []
    assert "My Telegram Bot" not in str(outsider.json())


def test_connected_railway_inventory_is_read_only(db_ready, monkeypatch):
    c = register("lab_railway")
    from portal.models import Customer
    with session_factory()() as db:
        customer = db.scalar(select(Customer).where(Customer.username == "lab_railway"))
        row = CloudOAuthConnection(customer_id=customer.id, provider="railway",
            remote_subject="railway-subject", remote_name="Team account",
            scopes="project:member", access_ciphertext=railway_oauth.encrypt("test-token"),
            refresh_ciphertext=None,
            expires_at=utcnow() + __import__("datetime").timedelta(minutes=30),
            created_at=utcnow(), updated_at=utcnow())
        db.add(row)
        db.commit()

    seen = []
    def fake_list(token):
        seen.append(token)
        return [{"id": "proj-1", "name": "Customer Railway", "services": [
                 {"id": "serv-1", "name": "Worker"}], "environments": []}]
    monkeypatch.setattr("api.bot_lab.list_projects", fake_list)
    response = c.get(BASE + "/railway/projects")
    assert response.status_code == 200, response.text
    assert response.json()["source"] == "railway_graphql"
    assert response.json()["projects"][0]["services"][0]["name"] == "Worker"
    assert seen == ["test-token"]
    assert "test-token" not in str(response.json())
    assert c.post(BASE + "/railway/projects").status_code == 405


def test_railway_provider_error_does_not_leak_token(db_ready, monkeypatch):
    c = register("lab_provider_fail")
    from portal.models import Customer
    with session_factory()() as db:
        customer = db.scalar(select(Customer).where(Customer.username == "lab_provider_fail"))
        db.add(CloudOAuthConnection(customer_id=customer.id, provider="railway",
            remote_subject="example-subject", remote_name="Example",
            scopes="", access_ciphertext=railway_oauth.encrypt("do-not-leak"),
            refresh_ciphertext=None,
            expires_at=utcnow() + __import__("datetime").timedelta(minutes=30),
            created_at=utcnow(), updated_at=utcnow()))
        db.commit()
    monkeypatch.setattr("api.bot_lab.list_projects",
                        lambda token: (_ for _ in ()).throw(RailwayReadError("provider unavailable")))
    response = c.get(BASE + "/railway/projects")
    assert response.status_code == 502
    assert "do-not-leak" not in response.text


def test_lab_assets_and_navigation():
    c = TestClient(app)
    assert c.get("/studio-assets/bot_lab.css").status_code == 200
    script = c.get("/studio-assets/bot_lab.js")
    assert script.status_code == 200
    for name in ("lab-bots-list", "lab-plans-list", "lab-flows-list",
                 "lab-check-railway", "railwayProjects"):
        assert name in script.text
    assert 'href="/bots/lab"' in c.get("/").text
