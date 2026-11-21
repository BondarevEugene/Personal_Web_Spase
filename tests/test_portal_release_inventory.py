"""Release inventory identifies missing modules without starting the application."""
from scripts import portal_release_inventory as release


def test_release_manifest_covers_all_product_layers():
    assert {"runtime", "public", "customer", "automation",
            "builder", "migration", "staging"} <= set(release.CRITICAL)


def test_inventory_reports_missing_files(tmp_path):
    report = release.inventory(tmp_path)
    assert report["ready"] is False
    assert not report["modules"]["runtime"]["ready"]
    assert any(not file["exists"] for file in report["modules"]["runtime"]["files"])


def test_inventory_reports_complete_synthetic_layout(tmp_path):
    for paths in release.CRITICAL.values():
        for path in paths:
            file = tmp_path / path
            file.parent.mkdir(parents=True, exist_ok=True)
            file.touch()
    report = release.inventory(tmp_path)
    assert report["ready"] is True
    assert all(section["ready"] for section in report["modules"].values())
