"""Public growth homepage: truthful ROI calculator, product paths, SEO discovery."""
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from omni_site.search_discovery import PUBLIC_PATHS, canonical_origin
from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_public_homepage_has_product_first_hero_and_real_conversion_routes():
    response = CLIENT.get("/")
    assert response.status_code == 200
    body = response.text
    assert "Меньше рутины. Больше возможностей." in body
    assert "Ваш бизнес." in body
    assert 'href="/studio#contact"' in body
    assert 'href="/architect"' in body
    assert 'id="benefit"' in body
    assert 'id="growth-calculator"' in body
    assert 'id="growth-money"' in body
    assert 'id="growth-solution"' in body
    assert 'href="/automation/studio"' in body
    assert 'public_growth.css?v=1' in body
    assert 'public_growth.js?v=1' in body
    assert 'name="description"' in body
    assert 'property="og:title"' in body
    assert body.count('<h1>') == 1


def test_calculator_markup_is_labeled_bounded_and_explicitly_an_estimate():
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    for key in ("growth-volume", "growth-minutes", "growth-rate", "growth-share"):
        assert f'for="{key}"' in source
        assert f'id="{key}"' in source
    assert 'min="1" max="1000000"' in source
    assert 'max="480"' in source
    assert "не обещание экономии" in source
    assert "не учтены" in source
    assert 'aria-live="polite"' in source
    assert 'aria-pressed="true"' in source
    script = (ROOT / "omni_site/static/public_growth.js").read_text(
        encoding="utf-8"
    )
    for endpoint in ("/account/projects", "/architect", "/automation/studio"):
        assert endpoint in script
    assert "fetch(" not in script
    assert "localStorage" not in script


def test_public_javascript_syntax_with_node_if_available():
    executable = shutil.which("node")
    if not executable:
        pytest.skip("Node.js is not installed; HTML and Python still tested.")
    file = ROOT / "omni_site/static/public_growth.js"
    done = subprocess.run([executable, "--check", str(file)],
                          capture_output=True, text=True, timeout=12)
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize("unsafe", [
    "", "http://omni.example.com", "https://user:pass@omni.example.com",
    "https://omni.example.com/secret", "https://omni.example.com/?tracking=1",
    "https://[broken",
])
def test_invalid_canonical_origins_are_rejected(unsafe):
    assert canonical_origin(unsafe) is None


def test_robots_and_sitemap_use_only_explicit_origin(monkeypatch):
    monkeypatch.delenv("OMNI_PUBLIC_BASE_URL", raising=False)
    r = CLIENT.get("/robots.txt")
    assert r.status_code == 200
    assert "Disallow: /account/" in r.text
    assert "Disallow: /support/" in r.text
    assert "Disallow: /api/" in r.text
    assert CLIENT.get("/sitemap.xml").status_code == 404

    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omni.example.com")
    robots = CLIENT.get("/robots.txt")
    assert "Sitemap: https://omni.example.com/sitemap.xml" in robots.text
    sitemap = CLIENT.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "application/xml" in sitemap.headers["content-type"]
    for path in PUBLIC_PATHS:
        assert "https://omni.example.com" + path in sitemap.text
    assert "/account" not in sitemap.text
    assert "/support" not in sitemap.text
    assert "/api/" not in sitemap.text


def test_public_growth_resources_resolve_and_have_accessible_layout():
    css = CLIENT.get("/studio-assets/public_growth.css")
    js = CLIENT.get("/studio-assets/public_growth.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert "prefers-reduced-motion" in css.text
    assert "max-width:750px" in css.text
    assert "aria-pressed" in js.text
