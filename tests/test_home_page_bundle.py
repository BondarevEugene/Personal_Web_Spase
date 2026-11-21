"""Public homepage bundle contract and non-regression checks."""
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.build_home_page_css import build
from server import app

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "omni_site" / "static"


def test_home_page_bundle_is_exactly_current():
    content = (STATIC / "home_page.bundle.css").read_text(encoding="utf-8")
    assert content == build()
    assert content.index("/* BEGIN site.css */") < content.index("/* BEGIN home_features.bundle.css */")
    assert ".growth-workbench" in content
    assert ".pf-hero" in content


def test_homepage_uses_one_css_request_without_losing_content():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.text.count('rel="stylesheet"') == 1
    assert 'href="/studio-assets/home_page.bundle.css?v=1"' in response.text
    assert 'href="/studio#contact"' in response.text
    assert 'id="growth-calculator"' in response.text
    asset = client.get("/studio-assets/home_page.bundle.css")
    assert asset.status_code == 200
    assert ".growth-workbench" in asset.text
