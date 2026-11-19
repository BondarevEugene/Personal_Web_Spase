"""Project file acceptance: strict ownership, contents, quotas, and safe download."""
from io import BytesIO
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from portal.db import engine, session_factory
from portal.models import ClientProject, ClientProjectAttachment, Customer
from portal.project_attachments import MAX_FILE, checked_data, safe_name
from server import app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def db_ready(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "file_security.sqlite3").as_posix()
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


def register(name):
    client = TestClient(app)
    client.get("/account/register")
    response = client.post("/account/register", follow_redirects=False, data={
        "csrf_token": client.cookies.get("omni_portal_csrf"),
        "username": name, "display_name": name,
        "organization": name + " org", "email": name + "@files.test",
        "password": "Strong-Password-2026",
        "password_repeat": "Strong-Password-2026",
    })
    assert response.status_code == 303, response.text
    return client


def token(client, url="/account/projects"):
    response = client.get(url)
    assert response.status_code == 200
    return client.cookies.get("omni_portal_csrf")


def create(client):
    response = client.post("/account/projects", follow_redirects=False, data={
        "csrf_token": token(client),
        "title": "Uploaded customer assets",
        "brief": "Securely store and share a bounded customer project document.",
    })
    assert response.status_code == 303, response.text
    with session_factory()() as db:
        project_id = db.scalar(select(ClientProject.id).where(
            ClientProject.title == "Uploaded customer assets"
        ))
    return project_id


def test_file_signature_size_and_safe_name():
    assert safe_name(r"C:\fakepath\readme.txt") == "readme.txt"
    assert checked_data("README.TXT", b"Hello, customer") == "text/plain"
    assert checked_data("doc.pdf", b"%PDF-1.4\n%%EOF") == "application/pdf"
    for name, data in [
        ("shell.exe", b"fake"),
        ("image.png", b"not an image"),
        ("image.jpg", b"not a photo"),
        ("report.pdf", b"not PDF"),
        ("text.txt", b"\x00\x01"),
        ("huge.txt", b"A" * (MAX_FILE + 1)),
    ]:
        with pytest.raises(Exception) as exc:
            checked_data(name, data)
        assert exc.value.status_code == 422


def test_customer_file_persists_and_is_private(db_ready, monkeypatch):
    client = register("attachmentowner")
    outsider = register("attachmentother")
    operator = register("attachmentstaff")
    project_id = create(client)
    url = "/account/projects/" + project_id + "/attachments"
    file_body = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"
    upload = client.post(url, data={"csrf_token": token(client)},
                         files={"uploaded": ("requirements.pdf", BytesIO(file_body),
                                             "application/pdf")},
                         follow_redirects=False)
    assert upload.status_code == 303, upload.text
    with session_factory()() as db:
        row = db.scalar(select(ClientProjectAttachment).where(
            ClientProjectAttachment.project_id == project_id
        ))
        attachment_id, hash_value = row.id, row.sha256
        assert row.data == file_body
        assert row.filename == "requirements.pdf"
        staff_id = db.scalar(select(Customer.id).where(
            Customer.username == "attachmentstaff"
        ))
    assert len(hash_value) == 64
    download = url + "/" + attachment_id
    received = client.get(download)
    assert received.status_code == 200
    assert received.content == file_body
    assert "attachment;" in received.headers["content-disposition"]
    assert received.headers["content-type"] == "application/octet-stream"
    assert "no-store" in received.headers["cache-control"]
    assert "requirements.pdf" in client.get("/account/projects/" + project_id).text

    assert outsider.get(download).status_code == 404
    assert outsider.post(url, data={"csrf_token": token(outsider)},
                         files={"uploaded": ("private.txt", b"stolen", "text/plain")}).status_code == 404
    assert operator.get("/support/projects/" + project_id
                        + "/attachments/" + attachment_id).status_code == 403
    monkeypatch.setenv("OMNI_SUPPORT_OPERATOR_IDS", staff_id)
    assert operator.get("/support/projects/" + project_id
                        + "/attachments/" + attachment_id).content == file_body


def test_upload_rejects_untrusted_files_and_missing_csrf(db_ready):
    owner = register("fileguard")
    project = create(owner)
    url = "/account/projects/" + project + "/attachments"
    assert owner.post(url, files={
        "uploaded": ("valid.txt", b"valid payload", "text/plain")
    }).status_code == 403
    assert owner.post(url, data={"csrf_token": token(owner)}, files={
        "uploaded": ("sneaky.pdf", b"not a PDF", "application/pdf")
    }).status_code == 422
    assert owner.post(url, data={"csrf_token": token(owner)}, files={
        "uploaded": ("huge.txt", b"x" * (MAX_FILE + 1), "text/plain")
    }).status_code == 422
    with session_factory()() as db:
        assert db.scalars(select(ClientProjectAttachment)).all() == []


def test_attachment_count_cap(db_ready):
    owner = register("filequota")
    project_id = create(owner)
    url = "/account/projects/" + project_id + "/attachments"
    for i in range(8):
        response = owner.post(url, data={"csrf_token": token(owner)},
                              files={"uploaded": (f"v{i}.txt", f"version {i}".encode(),
                                                  "text/plain")},
                              follow_redirects=False)
        assert response.status_code == 303
    denied = owner.post(url, data={"csrf_token": token(owner)},
                        files={"uploaded": ("ninth.txt", b"blocked", "text/plain")})
    assert denied.status_code == 413
