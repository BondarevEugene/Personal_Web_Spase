"""Full downloadable Blueprint delivery archive and integrity verification."""
import io
import json
import re
import zipfile
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient

from omni_site.blueprint_delivery import make_delivery_package
from server import app

CLIENT = TestClient(app)
URL = "/demo/blueprint/package"
BASE = {"sector": "crm", "team": "growth", "process": "manual", "priority": "control"}
FILES = {
    "README.md", "SPECIFICATION.md", "blueprint.json",
    "acceptance.json", "CHECKLIST.md", "manifest.json",
    "architecture.json", "milestones.json", "verification.json", "risks.json",
}


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation"])
def test_archive_download_for_every_product_and_manifest_integrity(sector):
    response = CLIENT.post(URL, data={**BASE, "sector": sector})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert re.fullmatch(
        r'attachment; filename="omnifactory-blueprint-[a-f0-9]{12}\.zip"',
        response.headers["content-disposition"],
    )
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == FILES
        manifest = json.loads(archive.read("manifest.json"))
        config = json.loads(archive.read("blueprint.json"))
        acceptance = json.loads(archive.read("acceptance.json"))
        assert config["sector"] == sector
        assert config["deployable"] is False
        assert config["revision"] == manifest["revision"]
        assert len(acceptance["items"]) >= 4
        assert set(manifest["files"]) == FILES - {"manifest.json"}
        for name in ("architecture.json", "milestones.json", "verification.json", "risks.json"):
            document = json.loads(archive.read(name))
            assert document["revision"] == manifest["revision"]
        assert json.loads(archive.read("architecture.json"))["deployable"] is False
        for filename, metadata in manifest["files"].items():
            data = archive.read(filename)
            assert metadata["sha256"] == sha256(data).hexdigest()
            assert metadata["bytes"] == len(data)
        assert b"OMNIFACTORY" in archive.read("README.md")


def test_archive_is_bitwise_deterministic_independent_of_checkbox_order():
    a = make_delivery_package(**BASE, integrations=("telegram", "payments"))
    b = make_delivery_package(**BASE, integrations=("payments", "telegram"))
    assert a.revision == b.revision
    assert a.content == b.content


@pytest.mark.parametrize("field", ["sector", "team", "process", "priority"])
def test_invalid_choice_rejected(field):
    response = CLIENT.post(URL, data={**BASE, field: "invalid"})
    assert response.status_code == 422


def test_duplicate_integration_and_missing_fields_rejected():
    assert CLIENT.post(
        URL, data={**BASE, "integration": ["telegram", "telegram"]},
    ).status_code == 422
    assert CLIENT.post(URL, data={"sector": "crm"}).status_code == 422
    assert CLIENT.get(URL).status_code == 405


def test_blueprint_form_exposes_package_without_javascript():
    html = CLIENT.post("/demo/blueprint", data=BASE).text
    assert 'formaction="/demo/blueprint/package"' in html
    assert "Скачать пакет проекта" in html
