"""Smoke tests for real platform navigation and template rendering."""
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_platform_matches_studio_visual_system():
    r = client.get("/")
    assert r.status_code == 200
    assert 'href="/studio-assets/site.css?v=3"' in r.text
    assert 'href="/studio-assets/platform.css?v=1"' in r.text
    assert 'href="/studio"' in r.text
    assert 'href="/builder_pro_final.html"' in r.text


def test_platform_css_is_served():
    r = client.get("/studio-assets/platform.css")
    assert r.status_code == 200
    assert "pf-module-grid" in r.text


def test_live_dashboard_is_full_page():
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "<!doctype html>" in r.text.lower()
    assert 'GET /health' in r.text
    assert "99.8%" not in r.text


def test_legacy_routes_render_instead_of_500():
    for path in ("/architect", "/admin", "/admin/", "/builder-pro",
                 "/builder_pro_final.html", "/projects", "/techkillers",
                 "/robotization", "/pages/builder_pro.html",
                 "/pages/projects.html", "/pages/techkillers.html"):
        r = client.get(path)
        assert r.status_code == 200, (path, r.status_code, r.text[:350])


def test_static_studio_does_not_change():
    r = client.get("/studio")
    assert r.status_code == 200
    assert "Архитектура." in r.text
