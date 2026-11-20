"""Accepted project handover ZIP regression tests."""
import hashlib
import io
import json
import zipfile
from datetime import datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from portal.project_archive import archive_bytes
from server import app


def fixture_project():
    stamp = datetime(2026, 11, 20)
    project = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        title="Customer project", brief="Delivery specification",
        status="accepted", created_at=stamp, updated_at=stamp, due_date=None,
    )
    document = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000002",
        document_kind="delivery", title="Final result", version=2,
        body="A verified result.",
    )
    return project, document


def test_zip_is_reproducible_and_hashes_verify():
    project, document = fixture_project()
    first = archive_bytes(project, [document], [], [], [])
    assert first == archive_bytes(project, [document], [], [], [])
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema"] == "omnifactory-project-archive-v1"
        for name, digest in manifest["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest
        assert archive.read("documents/" + document.id + ".txt") == b"A verified result."


def test_anonymous_archive_is_not_downloadable():
    response = TestClient(app).get(
        "/account/projects/00000000-0000-0000-0000-000000000001/archive",
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/account/login"


def test_archive_link_only_for_accepted_projects():
    from pathlib import Path

    html = (
        Path(__file__).resolve().parents[1]
        / "portal/templates/client_project_detail.html"
    ).read_text(encoding="utf-8")
    assert 'project.status == "accepted"' in html
    assert "/archive" in html
