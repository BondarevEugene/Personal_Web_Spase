"""Public trust center release: factual claims, SEO, navigation and no secrets."""
from pathlib import Path

from fastapi.testclient import TestClient

from omni_site.trust_content import PAGES, PAGE_BY_SLUG
from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_disclosures_have_sources_and_no_fabricated_certification():
    assert len(PAGES) == 3
    assert len(PAGE_BY_SLUG) == 3
    for item in PAGES:
        assert item.slug in PAGE_BY_SLUG
        assert len(item.sections) >= 4
        for section in item.sections:
            assert len(section.items) >= 3
            assert section.heading
            assert section.description
    security = PAGE_BY_SLUG["security"]
    body = " ".join(
        section.description + " ".join(section.items)
        for section in security.sections
    )
    assert "CSRF" in body
    assert "организации" in body
    assert "SOC 2" in body
    assert "не" in body.lower()


def test_trust_landing_is_public_and_links_to_real_cases_and_lead():
    result = CLIENT.get("/trust")
    assert result.status_code == 200, result.text[:400]
    assert result.text.count("<h1>") == 1
    assert 'href="/studio#contact"' in result.text
    assert 'href="/cases"' in result.text
    assert 'href="/journal"' in result.text
    assert 'name="description"' in result.text
    for item in PAGES:
        assert 'href="/trust/' + item.slug + '"' in result.text


def test_three_trust_detail_pages_have_accessible_headings_and_limits():
    for item in PAGES:
        response = CLIENT.get("/trust/" + item.slug)
        assert response.status_code == 200
        assert item.title in response.text
        assert item.summary in response.text
        assert response.text.count("<h1>") == 1
        assert 'href="/studio#contact"' in response.text
        assert 'href="/trust"' in response.text
        assert "не заявляются независимые аудиты" in response.text
        for section in item.sections:
            assert section.heading in response.text
            assert section.description in response.text
            assert section.items[0] in response.text
        assert 'aria-label="Разделы материала"' in response.text
    assert CLIENT.get("/trust/not-a-topic").status_code == 404


def test_public_growth_routes_link_to_trust():
    for url in ("/", "/services", "/cases", "/journal"):
        result = CLIENT.get(url)
        assert result.status_code == 200
        assert 'href="/trust"' in result.text, url
    home = CLIENT.get("/")
    for item in PAGES:
        assert 'href="/trust/' + item.slug + '"' in home.text


def test_sitemap_includes_only_public_trust_pages(monkeypatch):
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omni.example.com")
    response = CLIENT.get("/sitemap.xml")
    assert response.status_code == 200
    assert "<loc>https://omni.example.com/trust</loc>" in response.text
    for item in PAGES:
        assert "<loc>https://omni.example.com/trust/" + item.slug + "</loc>" in response.text
    assert "/account/" not in response.text
    monkeypatch.delenv("OMNI_PUBLIC_BASE_URL", raising=False)
    assert CLIENT.get("/sitemap.xml").status_code == 404


def test_trust_assets_resolve_and_contain_mobile_rules():
    for stylesheet in ("trust.css", "trust_home.css"):
        r = CLIENT.get("/studio-assets/" + stylesheet)
        assert r.status_code == 200
        assert "max-width:" in r.text
    assert "prefers-reduced-motion" in CLIENT.get(
        "/studio-assets/trust.css"
    ).text
    assert (ROOT / "omni_site/templates/trust_center.html").is_file()
    assert (ROOT / "omni_site/templates/trust_detail.html").is_file()
