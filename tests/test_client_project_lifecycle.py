"""Customer project lifecycle: migrations, isolation, operator workflow, acceptance."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from portal.db import engine, session_factory
from portal.models import Customer
from server import app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "client_projects.sqlite3").as_posix()
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


def register(username):
    client = TestClient(app)
    result = client.get("/account/register")
    assert result.status_code == 200
    token = client.cookies.get("omni_portal_csrf")
    result = client.post("/account/register", follow_redirects=False, data={
        "csrf_token": token,
        "username": username,
        "email": username + "@client.test",
        "display_name": "Client " + username,
        "organization": username + " org",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    })
    assert result.status_code == 303, result.text
    return client


def csrf(client):
    r = client.get("/account/projects")
    assert r.status_code == 200
    return {"csrf_token": client.cookies.get("omni_portal_csrf")}


def operator_csrf(client):
    client.get("/support/projects")
    return client.cookies.get("omni_portal_csrf")


def test_request_is_tenant_scoped_and_appears_on_dashboard(db_ready):
    owner = register("projectowner")
    other = register("projectother")
    new = owner.post("/account/projects", data={
        **csrf(owner), "title": "New custom automation",
        "brief": "Connect the customer workflow to an approved CRM.",
    }, follow_redirects=False)
    assert new.status_code == 303, new.text
    listing = owner.get("/account/projects")
    assert "New custom automation" in listing.text
    assert "New custom automation" in owner.get("/account").text
    assert "New custom automation" not in other.get("/account/projects").text
    assert "New custom automation" not in other.get("/account").text
    url = listing.text.split('href="/account/projects/')[1].split('"')[0]
    assert other.get("/account/projects/" + url).status_code == 404
    assert other.post("/account/projects/" + url + "/accept",
                      data=csrf(other)).status_code == 404


def test_operator_only_status_milestones_and_customer_acceptance(db_ready, monkeypatch):
    client = register("projectclient")
    operator = register("projectstaff")
    client.post("/account/projects", data={
        **csrf(client), "title": "Delivery automation",
        "brief": "Build a scripted workflow and test acceptance conditions.",
    })
    with session_factory()() as db:
        staff_id = db.scalar(select(Customer.id).where(Customer.username == "projectstaff"))
    assert operator.get("/support/projects").status_code == 403
    monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", staff_id)
    assert operator.get("/support/projects").status_code == 200
    from portal.models import ClientProject
    with session_factory()() as db:
        project_id = db.scalar(select(ClientProject.id).where(
            ClientProject.title == "Delivery automation"
        ))
    detail = "/support/projects/" + project_id

    def transition(target):
        return operator.post(detail + "/status", data={
            "csrf_token": operator_csrf(operator), "status": target,
        }, follow_redirects=False)

    assert transition("accepted").status_code == 409
    assert transition("planning").status_code == 303
    assert operator.post(detail + "/milestones", data={
        "csrf_token": operator_csrf(operator), "title": "Implementation",
        "details": "Implement the customer agreed functionality.",
    }, follow_redirects=False).status_code == 303

    from portal.models import ClientProjectMilestone, ClientProjectEvent
    with session_factory()() as db:
        stage_id = db.scalar(select(ClientProjectMilestone.id).where(
            ClientProjectMilestone.project_id == project_id
        ))
    assert transition("in_progress").status_code == 303
    assert transition("review").status_code == 409

    def stage(target):
        return operator.post(detail + "/milestones/" + stage_id, data={
            "csrf_token": operator_csrf(operator), "status": target,
        }, follow_redirects=False)

    assert stage("in_progress").status_code == 303
    assert stage("completed").status_code == 303
    assert transition("review").status_code == 303
    assert client.get("/account/projects/" + project_id).status_code == 200
    accepted = client.post("/account/projects/" + project_id + "/accept",
                           data=csrf(client), follow_redirects=False)
    assert accepted.status_code == 303, accepted.text
    assert transition("planning").status_code == 409
    with session_factory()() as db:
        assert db.scalar(select(ClientProject.status).where(
            ClientProject.id == project_id)) == "accepted"
        events = db.scalars(select(ClientProjectEvent).where(
            ClientProjectEvent.project_id == project_id)).all()
        assert [event.event_type for event in events].count("acceptance") == 1
        assert len(events) >= 6


def test_project_writes_require_csrf_and_operator_access(db_ready):
    user = register("projectsecurity")
    assert user.post("/account/projects", data={
        "title": "A valid project", "brief": "A sufficiently detailed request for work.",
    }).status_code == 403
    assert user.get("/support/projects").status_code == 403
    assert user.post("/support/projects/00000000-0000-0000-0000-000000000000/status",
                     data={"status": "planning"}).status_code == 403
