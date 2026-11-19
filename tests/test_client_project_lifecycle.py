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

    assigned = operator.post(detail + "/assignment", data={
        "csrf_token": operator_csrf(operator), "assignee_id": staff_id,
        "due_on": "2026-12-15",
    }, follow_redirects=False)
    assert assigned.status_code == 303, assigned.text
    assert "15.12.2026" in client.get("/account/projects/" + project_id).text
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


def test_versioned_specification_approval_and_inbox_is_tenant_scoped(
    db_ready, monkeypatch
):
    from portal.models import (
        ClientProject, ClientProjectApproval, ClientProjectDocument,
        ClientProjectNotification,
    )

    client = register("docowner")
    staff = register("docstaff")
    outsider = register("docoutsider")
    with session_factory()() as db:
        staff_id = db.scalar(select(Customer.id).where(
            Customer.username == "docstaff"
        ))
        client_id = db.scalar(select(Customer.id).where(
            Customer.username == "docowner"
        ))
    monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", staff_id)
    created = client.post("/account/projects", data={
        **csrf(client),
        "title": "Versioned specification contract",
        "brief": "A real customer project with approved requirements and tracked revisions.",
    }, follow_redirects=False)
    assert created.status_code == 303
    with session_factory()() as db:
        project_id = db.scalar(select(ClientProject.id).where(
            ClientProject.title == "Versioned specification contract"
        ))
    op_page = "/support/projects/" + project_id
    customer_page = "/account/projects/" + project_id

    def publish(body):
        return staff.post(op_page + "/documents", data={
            "csrf_token": operator_csrf(staff),
            "kind": "specification", "title": "Product specification",
            "body": body,
        }, follow_redirects=False)

    assert publish("The first immutable technical specification for this order.").status_code == 303
    with session_factory()() as db:
        docs = db.scalars(select(ClientProjectDocument).where(
            ClientProjectDocument.project_id == project_id
        )).all()
        assert len(docs) == 1
        first_id = docs[0].id
        assert docs[0].version == 1
    assert "Product specification" in client.get(customer_page).text
    assert "Product specification" not in outsider.get("/account/notifications").text
    assert outsider.get(customer_page).status_code == 404
    assert outsider.post(
        customer_page + "/documents/" + first_id + "/approve",
        data=csrf(outsider)
    ).status_code == 404

    approve_url = customer_page + "/documents/" + first_id + "/approve"
    assert client.post(approve_url, data={}).status_code == 403
    approved = client.post(approve_url, data=csrf(client), follow_redirects=False)
    assert approved.status_code == 303, approved.text
    # Approval is idempotent and never creates a duplicate ledger record.
    assert client.post(approve_url, data=csrf(client),
                       follow_redirects=False).status_code == 303
    with session_factory()() as db:
        assert len(db.scalars(select(ClientProjectApproval)).all()) == 1

    assert publish("A second, distinct immutable revision requiring renewed approval.").status_code == 303
    with session_factory()() as db:
        versions = db.scalars(select(ClientProjectDocument).where(
            ClientProjectDocument.project_id == project_id
        ).order_by(ClientProjectDocument.version)).all()
        second_id = versions[-1].id
        assert [doc.version for doc in versions] == [1, 2]
        assert versions[0].body.startswith("The first")
    assert client.post(approve_url, data=csrf(client)).status_code == 409

    # Client inbox is per recipient; a different organization cannot mark it read.
    inbox = client.get("/account/notifications")
    assert inbox.status_code == 200
    assert "Новая версия документа" in inbox.text
    with session_factory()() as db:
        unread = db.scalar(select(ClientProjectNotification.id).where(
            ClientProjectNotification.recipient_id == client_id,
            ClientProjectNotification.read_at.is_(None)
        ).limit(1))
        assert unread is not None
    assert outsider.post(
        "/account/notifications/" + unread + "/read", data=csrf(outsider)
    ).status_code == 404
    done = client.post(
        "/account/notifications/" + unread + "/read",
        data=csrf(client), follow_redirects=False
    )
    assert done.status_code == 303
    with session_factory()() as db:
        notice = db.get(ClientProjectNotification, unread)
        assert notice.read_at is not None
    assert client.post(
        customer_page + "/documents/" + second_id + "/approve",
        data=csrf(client), follow_redirects=False
    ).status_code == 303


def test_operator_documents_are_csrf_protected_and_bound_to_real_projects(
    db_ready, monkeypatch
):
    staff = register("securestaff")
    client = register("secureclient")
    with session_factory()() as db:
        staff_id = db.scalar(select(Customer.id).where(
            Customer.username == "securestaff"
        ))
    created = client.post("/account/projects", data={
        **csrf(client), "title": "A secure order",
        "brief": "Security and access test of protected document endpoints.",
    })
    assert created.status_code == 200
    from portal.models import ClientProject
    with session_factory()() as db:
        project_id = db.scalar(select(ClientProject.id).where(
            ClientProject.title == "A secure order"
        ))
    url = "/support/projects/" + project_id + "/documents"
    document = {
        "kind": "specification", "title": "Requirements",
        "body": "This document contains bounded text and a recorded version.",
    }
    assert staff.post(url, data=document).status_code == 403
    monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", staff_id)
    assert staff.post(url, data=document).status_code == 403
    assert staff.post(url, data={
        **{"csrf_token": operator_csrf(staff)}, **document
    }, follow_redirects=False).status_code == 303
