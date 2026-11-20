"""Public case catalog acceptance: real routes, source links and no fake screenshots."""
from pathlib import Path

from fastapi.testclient import TestClient

from omni_site.case_library import CASES, CASE_BY_SLUG, CATEGORIES
from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_cases_are_first_party_and_explicitly_limit_claims():
    assert len(CASES) == 4
    assert len(CASE_BY_SLUG) == len(CASES)
    assert CATEGORIES[0] == "Все"
    for case in CASES:
        assert case.product_url.startswith("/")
        assert case.source_url.startswith("https://github.com/BondarevEugene/")
        assert len(case.scope) >= 3
        assert len(case.limitations) >= 2
        assert case.diagram in {"flow", "milestones", "telegram", "automation"}
        assert case.category in CATEGORIES


def test_public_library_filter_and_real_product_links_render():
    page = CLIENT.get("/cases")
    assert page.status_code == 200
    assert 'data-case-filter="Все"' in page.text
    assert 'data-case-category=' in page.text
    assert "не скриншоты" in page.text.lower()
    for case in CASES:
        assert 'href="/cases/' + case.slug + '"' in page.text
        assert 'href="' + case.product_url + '"' in page.text
        assert case.title in page.text
    assert 'href="/studio#contact"' in page.text


def test_individual_case_pages_do_not_claim_deployed_instances():
    for case in CASES:
        page = CLIENT.get("/cases/" + case.slug)
        assert page.status_code == 200, page.text[:400]
        assert case.title in page.text
        assert case.problem in page.text
        assert case.approach in page.text
        assert case.scope[0] in page.text
        assert case.limitations[0] in page.text
        assert 'href="' + case.source_url + '"' in page.text
        assert 'href="/journal/' + case.journal_slug + '"' in page.text
        assert "NOT A SCREENSHOT" in page.text
        assert 'href="/studio#contact"' in page.text
    assert CLIENT.get("/cases/unknown-product").status_code == 404
    assert CLIENT.get("/cases/%3Cscript%3E").status_code == 404


def test_cases_discoverable_from_existing_platform_pages():
    home = CLIENT.get("/")
    assert home.status_code == 200
    assert 'href="/cases"' in home.text
    for case in CASES[:3]:
        assert 'href="/cases/' + case.slug + '"' in home.text
    projects = CLIENT.get("/projects")
    assert projects.status_code == 200
    assert 'href="/cases"' in projects.text


def test_sitemap_contains_only_public_case_urls(monkeypatch):
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omni.example.com")
    sitemap = CLIENT.get("/sitemap.xml")
    assert sitemap.status_code == 200
    assert "https://omni.example.com/cases" in sitemap.text
    for case in CASES:
        assert "https://omni.example.com/cases/" + case.slug in sitemap.text
    assert "/account/" not in sitemap.text
    monkeypatch.delenv("OMNI_PUBLIC_BASE_URL", raising=False)
    assert CLIENT.get("/sitemap.xml").status_code == 404


def test_progressive_enhancement_has_no_network_tracking():
    css = CLIENT.get("/studio-assets/case_library.css")
    js = CLIENT.get("/studio-assets/case_library.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert "prefers-reduced-motion" in css.text
    assert "max-width:620px" in css.text
    assert 'aria-pressed' in js.text
    assert "fetch(" not in js.text
    assert "localStorage" not in js.text
    assert (ROOT / "omni_site/templates/_case_diagram.html").exists()
