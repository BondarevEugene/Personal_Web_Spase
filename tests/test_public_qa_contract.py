"""Fast guardrails for the browser/asset audits; no Chromium needed."""
from pathlib import Path

import pytest

from scripts.public_asset_budget import AssetParser, collect
from scripts.public_ux_audit import ROUTES, VIEWPORTS, summarize, validate_base_url


@pytest.mark.parametrize("url", [
    "https://example.com",
    "http://example.com:8765",
    "http://127.0.0.1",
    "http://127.0.0.1:8765/private",
    "http://127.0.0.1:8765?token=secret",
    "http://evil@127.0.0.1:8765",
])
def test_browser_audit_accepts_only_explicit_loopback_url(url):
    with pytest.raises(ValueError):
        validate_base_url(url)


def test_browser_audit_has_full_mobile_and_desktop_matrix():
    assert validate_base_url(
        "http://127.0.0.1:8765/"
    ) == "http://127.0.0.1:8765"
    assert VIEWPORTS == (360, 430, 768, 1440)
    for route in ("/", "/demo", "/services", "/cases", "/trust"):
        assert route in ROUTES
    result = summarize([
        {"route": "/", "width": 360, "issues": []},
        {"route": "/demo", "width": 430, "issues": ["menu broken"]},
    ])
    assert result["checked"] == 2
    assert result["failed"] == 1
    assert result["failures"][0]["route"] == "/demo"


def test_asset_parser_only_collects_local_studio_assets():
    parser = AssetParser()
    parser.feed(
        '<link rel="stylesheet" href="/studio-assets/site.css?v=3">'
        '<script defer src="/studio-assets/demo.js?v=1"></script>'
        '<script src="https://analytics.invalid/tracker.js"></script>'
        '<a href="/account">Private</a>'
    )
    assert parser.paths == {
        "/studio-assets/site.css?v=3",
        "/studio-assets/demo.js?v=1",
    }


def test_public_asset_inventory_has_no_missing_resources():
    data = collect()
    assert data["page_count"] == 7
    assert data["asset_count"] >= 7
    assert data["unique_asset_bytes"] > 0
    assert data["failures"] == []
    assert all(
        item["path"].startswith("/studio-assets/")
        for item in data["assets"]
    )


def test_browser_quality_workflow_is_defined_and_not_production_tracking():
    root = Path(__file__).resolve().parents[1]
    workflow = (
        root / ".github/workflows/public_browser_quality.yml"
    ).read_text(encoding="utf-8")
    assert "python -m ruff check" in workflow
    assert "scripts/public_ux_audit.py" in workflow
    assert "scripts/public_asset_budget.py" in workflow
    assert "python -m scripts.public_asset_budget" in workflow
    assert "python -m scripts.public_ux_audit" in workflow
    assert "upload-artifact@v4" in workflow
    assert "feat/graph-runtime-incident-triage-20261121" in workflow
    script = (
        root / "scripts/public_ux_audit.py"
    ).read_text(encoding="utf-8")
    assert "page.screenshot" in script
    assert "pageerror" in script
    assert "horizontal overflow" in script
    assert "localStorage" not in script
    assert "http://127.0.0.1:8765" in script
