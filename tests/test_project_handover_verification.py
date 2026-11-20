"""Accepted delivery gate and offline ZIP integrity verification."""
import io
import json
import zipfile

from portal.project_archive import archive_bytes
from scripts.verify_project_archive import verify_archive
from tests.test_project_archive import fixture_project


def test_generated_handover_verifies(tmp_path):
    project, document = fixture_project()
    archive_path = tmp_path / "handover.zip"
    archive_path.write_bytes(archive_bytes(project, [document], [], [], []))
    assert verify_archive(archive_path) == []


def test_modified_archive_is_rejected(tmp_path):
    project, document = fixture_project()
    original = archive_bytes(project, [document], [], [], [])
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(original)) as source:
        with zipfile.ZipFile(output, "w") as target:
            for name in source.namelist():
                data = source.read(name)
                if name.endswith(".txt") and name.startswith("documents/"):
                    data = b"Tampered document"
                target.writestr(name, data)
    archive_path = tmp_path / "tampered.zip"
    archive_path.write_bytes(output.getvalue())
    assert any("SHA-256 mismatch" in error for error in verify_archive(archive_path))


def test_archive_without_manifest_is_rejected(tmp_path):
    archive_path = tmp_path / "missing.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("project.json", json.dumps({"id": "x"}))
    assert verify_archive(archive_path) == ["Missing manifest.json"]


def test_archive_with_unsafe_path_is_rejected(tmp_path):
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.txt", "bad")
    assert verify_archive(archive_path) == ["Unsafe ZIP path or directory entry"]


def test_both_review_and_accept_require_delivery_document():
    from inspect import getsource

    from portal.client_projects import accept_project, update_status

    assert "Опубликуйте описание результата перед приёмкой" in getsource(accept_project)
    assert "Опубликуйте описание результата перед приёмкой" in getsource(update_status)
