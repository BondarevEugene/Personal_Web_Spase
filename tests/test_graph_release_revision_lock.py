"""Release ZIP must match the exact persisted, customer-owned graph revision."""
import io
import zipfile

from fastapi.testclient import TestClient

from server import app
from tests.test_builder_projects import BASE, SCENARIO, csrf, db_ready, register


def test_saved_export_requires_revision_and_rejects_stale_or_foreign(db_ready):
    owner = register("release_owner", "release-owner@builder.test")
    other = register("release_other", "release-other@builder.test")
    created = owner.post(BASE, headers=csrf(owner), json={"scenario": SCENARIO})
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    revision = created.json()["revision"]
    url = BASE + "/" + project_id + "/export"

    assert TestClient(app).get(url).status_code == 401
    assert other.get(url, headers={"If-Match": revision}).status_code == 404
    assert owner.get(url).status_code == 428
    assert owner.get(url, headers={"If-Match": "0" * 64}).status_code == 409

    result = owner.get(url, headers={"If-Match": revision})
    assert result.status_code == 200, result.text
    assert result.headers["x-omni-project-revision"] == revision
    assert result.headers["cache-control"] == "no-store"
    with zipfile.ZipFile(io.BytesIO(result.content)) as archive:
        assert "bot.py" in archive.namelist()
        assert "smoke.py" in archive.namelist()
        assert ".github/workflows/verify.yml" in archive.namelist()

    updated = owner.put(
        BASE + "/" + project_id,
        headers={**csrf(owner), "If-Match": revision},
        json={"scenario": {**SCENARIO, "name": "Revised release"}},
    )
    assert updated.status_code == 200, updated.text
    new_revision = updated.json()["revision"]
    assert new_revision != revision
    assert owner.get(url, headers={"If-Match": revision}).status_code == 409
    latest = owner.get(url, headers={"If-Match": new_revision})
    assert latest.status_code == 200
    assert latest.headers["x-omni-project-revision"] == new_revision


def test_editor_releases_saved_revision_only():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] /
              "omni_site/static/graph_project_editor.js").read_text(encoding="utf-8")
    assert 'if (dirty) {' in source
    assert 'headers: {"If-Match": project.revision}' in source
    assert '"/export"' in source
    assert 'X-Omni-Project-Revision' in source
