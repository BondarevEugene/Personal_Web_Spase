"""Homepage resource budget and exact-order generated CSS contract."""
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.build_home_css import OUTPUT, SOURCES, STATIC, build
from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_homepage_has_exactly_two_stylesheets_and_bundle_is_reachable():
    page = CLIENT.get("/")
    assert page.status_code == 200
    html = page.text
    assert html.count('rel="stylesheet"') == 2
    assert 'href="/studio-assets/site.css?v=3"' in html
    assert 'href="/studio-assets/home_features.bundle.css?v=1"' in html
    for source in SOURCES:
        assert f'href="/studio-assets/{source}' not in html
    bundled = CLIENT.get("/studio-assets/" + OUTPUT)
    assert bundled.status_code == 200
    assert bundled.text == build()


def test_feature_sources_and_css_order_are_unchanged():
    generated = (STATIC / OUTPUT).read_text(encoding="utf-8")
    assert generated == build()
    indices = [generated.index(f"/* BEGIN {source} */") for source in SOURCES]
    assert indices == sorted(indices)
    assert len(set(indices)) == len(SOURCES)
    for source in SOURCES:
        assert f"/* END {source} */" in generated
        assert (STATIC / source).is_file()
        assert CLIENT.get("/studio-assets/" + source).status_code == 200


def test_bundle_does_not_add_external_css_or_javascript():
    compiled = build()
    assert "@import" not in compiled
    assert "<script" not in compiled
    assert "url(http" not in compiled.lower()
    assert (ROOT / "omni_site/static/site.css").is_file()


def test_other_public_pages_reuse_shared_base_stylesheet():
    for path in ("/services", "/cases", "/trust", "/journal", "/demo"):
        page = CLIENT.get(path)
        assert page.status_code == 200
        assert 'href="/studio-assets/site.css?v=3"' in page.text
        assert "home_features.bundle.css" not in page.text


def test_existing_homepage_interactions_remain_in_place():
    html = CLIENT.get("/").text
    assert 'src="/studio-assets/site.js?v=3"' in html
    assert 'src="/studio-assets/public_growth.js?v=1"' in html
    assert 'src="/studio-assets/unified_shell.js?v=1"' in html
    for path in ("/demo", "/services", "/cases", "/studio"):
        assert f'href="{path}"' in html
