"""Release candidate acceptance loop: requested → review → revisions → accepted."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from portal.db import engine, session_factory
from portal.models import (
    ClientProject, ClientProjectEvent, ClientProjectMilestone, Customer,
)
from server import app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "rc_acceptance.sqlite3").as_posix()
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


def signup(name):
    client = TestClient(app)
    assert client.get("/account/register").status_code == 200
    response = client.post("/account/register", data={
        "csrf_token": client.cookies.get("omni_portal_csrf"),
        "username": name, "display_name": name,
        "email": name + "@release.test", "organization": name + " org",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    }, follow_redirects=False)
    assert response.status_code == 303, response.text
    return client


def csrf(client, url):
    response = client.get(url)
    assert response.status_code == 200, response.text[:500]
    return client.cookies.get("omni_portal_csrf")


def test_full_delivery_revision_and_final_acceptance_cycle(db_ready, monkeypatch):
    owner = signup("rccustomer")
    staff = signup("rcoperator")
    outsider = signup("rcoutsider")
    with session_factory()() as db:
        staff_id = db.scalar(select(Customer.id).where(
            Customer.username == "rcoperator"
        ))
    monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", staff_id)

    result = owner.post("/account/projects", follow_redirects=False, data={
        "csrf_token": csrf(owner, "/account/projects"),
        "title": "Final delivery process",
        "brief": "Create a real deliverable and test review, revisions and acceptance.",
    })
    assert result.status_code == 303
    with session_factory()() as db:
        project_id = db.scalar(select(ClientProject.id).where(
            ClientProject.title == "Final delivery process"
        ))
    client_url = "/account/projects/" + project_id
    operator_url = "/support/projects/" + project_id

    def status(value):
        return staff.post(operator_url + "/status", follow_redirects=False, data={
            "csrf_token": csrf(staff, operator_url), "status": value,
        })

    assert status("planning").status_code == 303
    created = staff.post(operator_url + "/milestones", follow_redirects=False,
                         data={"csrf_token": csrf(staff, operator_url),
                               "title": "Final acceptance test",
                               "details": "Deliver and validate the final project result."})
    assert created.status_code == 303
    with session_factory()() as db:
        milestone_id = db.scalar(select(ClientProjectMilestone.id).where(
            ClientProjectMilestone.project_id == project_id
        ))

    def milestone(value):
        return staff.post(operator_url + "/milestones/" + milestone_id,
                          follow_redirects=False,
                          data={"csrf_token": csrf(staff, operator_url),
                                "status": value})

    assert status("in_progress").status_code == 303
    assert milestone("in_progress").status_code == 303
    assert milestone("completed").status_code == 303
    assert status("review").status_code == 303
    assert "request-changes" in owner.get(client_url).text

    message = "Change the notification copy and verify the final PDF layout."
    revision = owner.post(client_url + "/request-changes",
                          follow_redirects=False,
                          data={"csrf_token": csrf(owner, client_url),
                                "comment": message})
    assert revision.status_code == 303, revision.text
    with session_factory()() as db:
        assert db.get(ClientProject, project_id).status == "in_progress"
        events = db.scalars(select(ClientProjectEvent).where(
            ClientProjectEvent.project_id == project_id,
            ClientProjectEvent.event_type == "revision_requested",
        )).all()
        assert len(events) == 1
        assert message in events[0].summary
    assert "request-changes" not in owner.get(client_url).text
    assert owner.post(client_url + "/request-changes",
                      data={"csrf_token": csrf(owner, client_url),
                            "comment": message}).status_code == 409
    assert outsider.get(client_url).status_code == 404
    assert outsider.post(client_url + "/request-changes",
                         data={"csrf_token": csrf(outsider, "/account/projects"),
                               "comment": message}).status_code == 404
    assert owner.post(client_url + "/accept",
                      data={"csrf_token": csrf(owner, client_url)}).status_code == 409

    assert milestone("in_progress").status_code == 303
    assert milestone("completed").status_code == 303
    assert status("review").status_code == 303
    accepted = owner.post(client_url + "/accept", follow_redirects=False,
                          data={"csrf_token": csrf(owner, client_url)})
    assert accepted.status_code == 303
    with session_factory()() as db:
        assert db.get(ClientProject, project_id).status == "accepted"
        events = db.scalars(select(ClientProjectEvent).where(
            ClientProjectEvent.project_id == project_id
        )).all()
        assert sum(item.event_type == "revision_requested" for item in events) == 1
        assert sum(item.event_type == "acceptance" for item in events) == 1


def test_change_request_rejects_missing_csrf_and_short_text(db_ready):
    owner = signup("rcvalidation")
    with session_factory()() as db:
        customer = db.scalar(select(Customer).where(
            Customer.username == "rcvalidation"
        ))
        project = ClientProject(
            org_id=customer.org_id, created_by_id=customer.id,
            title="Already on review", brief="Customer review validation.",
            status="review",
        )
        db.add(project)
        db.commit()
        project_id = project.id
    url = "/account/projects/" + project_id
    assert owner.post(url + "/request-changes",
                      data={"comment": "Legitimate revision request."}).status_code == 403
    assert owner.post(url + "/request-changes",
                      data={"csrf_token": csrf(owner, url),
                            "comment": "too short"}).status_code == 422
    assert owner.post(url + "/request-changes",
                      data={"csrf_token": csrf(owner, url),
                            "comment": "x" * 2001}).status_code == 422
