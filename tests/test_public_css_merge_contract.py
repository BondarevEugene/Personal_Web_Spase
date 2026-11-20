"""Regression contract for the merged homepage CSS pipeline (PR #74 + #76)."""
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.build_home_css import OUTPUT, SOURCES, STATIC, build
from server import app

ROOT = Path(__file__).resolve().parents[1]


def test_homepage_uses_only_existing_two_ordered_stylesheets():
    html = TestClient(app).get("/")
    assert html.status_code == 200
    styles = [
        line.strip()
        for line in html.text.splitlines()
        if '<link rel="stylesheet"' in line
    ]
    assert len(styles) == 2
    assert '/studio-assets/site.css?v=3' in styles[0]
    assert '/studio-assets/home_features.bundle.css?v=1' in styles[1]
    assert 'home.bundle.css' not in html.text


def test_generated_feature_bundle_is_byte_identical_and_ordered():
    actual = (STATIC / OUTPUT).read_text(encoding="utf-8")
    assert actual == build()
    assert len(SOURCES) == len(set(SOURCES)) == 9
    markers = [actual.index(f"/* BEGIN {name} */") for name in SOURCES]
    assert markers == sorted(markers)
    assert "site.css" not in SOURCES


def test_public_blueprint_and_original_css_remain_available():
    client = TestClient(app)
    assert client.get("/demo/blueprint").status_code == 200
    for asset in ("site.css", OUTPUT):
        response = client.get(f"/studio-assets/{asset}")
        assert response.status_code == 200
        assert response.text
