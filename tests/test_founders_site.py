"""Founders presentation contract: routes and image references, without identities."""
from fastapi.testclient import TestClient
from server import app


def test_founders_on_homepage():
    with TestClient(app) as client:
        page=client.get("/")
        assert page.status_code==200
        html=page.text
        assert 'id="founders"' in html
        assert 'id="founders-heading"' in html
        assert '/studio-assets/founders/founder-01.webp' in html
        assert '/studio-assets/founders/founder-02.webp' in html
        assert 'founders.css?v=1' in html
        assert 'href="#founders"' in html
        assert html.count('class="omni-founder-card"') == 2


def test_founders_styles_are_scoped():
    with TestClient(app) as client:
        r=client.get("/studio-assets/founders.css")
        assert r.status_code==200
        assert ".omni-founders-grid" in r.text
        assert "@media(max-width:540px)" in r.text
