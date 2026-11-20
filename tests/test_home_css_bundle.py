"""Homepage consolidation: deterministic output, CSS cascade, public routes."""
from pathlib import Path

from fastapi.testclient import TestClient

from scripts.build_public_styles import BUNDLE, HOME_CSS, render_bundle
from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_homepage_has_one_local_stylesheet_without_broken_links():
    result = CLIENT.get("/")
    assert result.status_code == 200
    assert result.text.count('rel="stylesheet"') == 1
    assert 'href="/studio-assets/home.bundle.css?v=1"' in result.text
    for name in HOME_CSS:
        assert f'href="/studio-assets/{name}' not in result.text
    assert 'href="/studio#contact"' in result.text
    assert 'href="/demo"' in result.text
    assert 'id="growth-calculator"' in result.text


def test_bundle_is_current_and_preserves_original_order():
    expected = render_bundle()
    assert BUNDLE.exists()
    assert BUNDLE.read_bytes() == expected
    content = expected.decode("utf-8")
    positions = [content.index(f"/* BEGIN {item} */") for item in HOME_CSS]
    assert positions == sorted(positions)
    assert len(positions) == 10
    assert content.count("/* BEGIN ") == 10
    assert content.count("/* END ") == 10
    assert content.index("@import") < content.index(":root{")
    assert "body{margin:0" in content
    assert ".omni-mobile-contact" in content
    assert ".omni-hero-pathways" in content


def test_compiled_css_is_served_successfully():
    response = CLIENT.get("/studio-assets/home.bundle.css?v=1")
    assert response.status_code == 200
    assert response.content == BUNDLE.read_bytes()
    assert len(response.content) < 700_000
    assert "text/css" in response.headers["content-type"]


def test_studio_and_secondary_pages_keep_existing_styles():
    studio = CLIENT.get("/studio")
    assert studio.status_code == 200
    assert 'href="/studio-assets/site.css?v=3"' in studio.text
    assert 'home.bundle.css' not in studio.text
    services = CLIENT.get("/services")
    assert services.status_code == 200
    assert 'href="/studio-assets/services.css?v=1"' in services.text
    assert 'home.bundle.css' not in services.text
    assert (ROOT / "omni_site/static/site.css").exists()


def test_home_assets_keep_all_existing_interactive_scripts():
    markup = CLIENT.get("/").text
    for name in (
        "site.js?v=3", "unified_shell.js?v=1", "public_growth.js?v=1",
    ):
        assert f'src="/studio-assets/{name}"' in markup
    assert "founder-01.webp" in markup
    assert "founder-02.webp" in markup
    assert 'loading="lazy"' in markup
