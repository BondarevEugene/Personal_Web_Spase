"""End-to-end deterministic Blueprint ZIP and offline verification."""
import io
import json
import zipfile

import pytest

from omni_site.blueprint_delivery import make_delivery_package
from scripts.verify_blueprint_package import PackageError, verify_package


@pytest.mark.parametrize("sector", ["crm", "telegram", "automation", "ai"])
def test_all_product_sectors_have_verified_architecture_package(sector):
    kwargs = dict(
        sector=sector, team="growth", process="manual", priority="control",
        integrations=("telegram", "database"),
    )
    package = make_delivery_package(**kwargs)
    assert package.content == make_delivery_package(**kwargs).content
    result = verify_package(package.content)
    assert result["ok"] and result["revision"] == package.revision
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        architecture = json.loads(archive.read("architecture.json"))
        milestones = json.loads(archive.read("milestones.json"))
        verification = json.loads(archive.read("verification.json"))
        risks = json.loads(archive.read("risks.json"))
        assert architecture["deployable"] is False
        assert len(architecture["nodes"]) >= 4
        assert len(architecture["links"]) == len(architecture["nodes"]) - 1
        assert all(not item["connected"] for item in architecture["integrations"])
        assert len(milestones["items"]) == 5
        assert milestones["items"][1]["depends_on"] == ["MS-001"]
        assert all(item["result"] == "not_run" for item in verification["checks"])
        assert all(item["status"] == "open" for item in risks["items"])


def test_package_rejects_invalid_or_unsafe_archive():
    with pytest.raises(PackageError):
        verify_package(b"not-a-zip")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../unsafe", "data")
        archive.writestr("manifest.json", "{}")
    with pytest.raises(PackageError, match="Unsafe archive path"):
        verify_package(buffer.getvalue())


def test_package_rejects_corrupted_manifest():
    package = make_delivery_package(
        sector="crm", team="solo", process="new", priority="speed",
    )
    with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
        data = {name: archive.read(name) for name in archive.namelist()}
    data["SPECIFICATION.md"] = b"tampered"
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, content in data.items():
            archive.writestr(name, content)
    with pytest.raises(PackageError, match="Checksum mismatch"):
        verify_package(output.getvalue())
