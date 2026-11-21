"""Services site: factual product pages, search discovery, and real inquiry path."""
from pathlib import Path
from urllib.parse import quote

from fastapi.testclient import TestClient

from omni_site.services_catalog import SERVICES, SERVICE_BY_SLUG
from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_services_are_unique_and_have_relevant_existing_case_links():
    assert len(SERVICES) == 4
    assert len(SERVICE_BY_SLUG) == len(SERVICES)
    for service in SERVICES:
        assert service.case_url.startswith("/cases/")
        assert service.journal_url.startswith("/journal/")
        assert service.lead_topic in {
            "CRM / управление бизнесом",
            "Telegram Bot / Mini App",
            "AI / автоматизация",
            "AI / интеллектуальные системы",
        }
        assert len(service.deliverables) >= 4
        assert len(service.process) >= 4
        assert len(service.limitations) >= 3
        assert len(service.questions) >= 3
        assert CLIENT.get(service.case_url).status_code == 200
        assert CLIENT.get(service.journal_url).status_code == 200


def test_directory_and_four_pages_serve_unique_seo_copy():
    index = CLIENT.get("/services")
    assert index.status_code == 200
    assert "Решение вашей задачи" in index.text
    assert 'href="/studio#contact"' in index.text
    assert '<meta name="description"' in index.text
    assert 'href="/cases"' in index.text
    assert index.text.count("<h1>") == 1
    for service in SERVICES:
        assert 'href="/services/' + service.slug + '"' in index.text
        detail = CLIENT.get("/services/" + service.slug)
        assert detail.status_code == 200, detail.text[:500]
        assert service.title in detail.text
        assert service.summary in detail.text
        assert service.limitations[0] in detail.text
        assert service.deliverables[0] in detail.text
        assert service.questions[0][0] in detail.text
        assert detail.text.count("<h1>") == 1
        assert 'href="' + service.case_url + '"' in detail.text
        assert 'href="' + service.journal_url + '"' in detail.text
        assert 'href="/studio?topic=' + quote(
            service.lead_topic, safe=""
        ) + '#contact"' in detail.text or (
            '/studio?topic=' in detail.text and service.lead_topic.split()[0] in detail.text
        )
    assert CLIENT.get("/services/unknown").status_code == 404


def test_search_discovery_only_exposes_public_services(monkeypatch):
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omni.example.com")
    response = CLIENT.get("/sitemap.xml")
    assert response.status_code == 200
    assert "<loc>https://omni.example.com/services</loc>" in response.text
    for service in SERVICES:
        assert "<loc>https://omni.example.com/services/" + service.slug + "</loc>" in response.text
    assert "/account/" not in response.text
    monkeypatch.delenv("OMNI_PUBLIC_BASE_URL", raising=False)
    assert CLIENT.get("/sitemap.xml").status_code == 404


def test_homepage_cases_and_studio_are_connected():
    homepage = CLIENT.get("/")
    assert homepage.status_code == 200
    for service in SERVICES:
        assert 'href="/services/' + service.slug + '"' in homepage.text
    assert 'href="/services"' in homepage.text
    assert 'href="/services"' in CLIENT.get("/cases").text

    studio = CLIENT.get("/studio")
    assert studio.status_code == 200
    for service in SERVICES:
        assert service.lead_topic in studio.text
    script = (ROOT / "omni_site/static/site.js").read_text(encoding="utf-8")
    assert "URLSearchParams(window.location.search)" in script
    assert "option.value === leadTopic" in script
    assert "if (matchingOption)" in script
    assert "topicSelect.value = matchingOption.value" in script


def test_services_assets_have_mobile_and_keyboard_support():
    for path in ("services.css", "services_home.css"):
        response = CLIENT.get("/studio-assets/" + path)
        assert response.status_code == 200
        assert "max-width:" in response.text
    assert "prefers-reduced-motion" in CLIENT.get(
        "/studio-assets/services.css"
    ).text
    markup = CLIENT.get("/services")
    assert 'class="skip-link"' in markup.text
    detail = CLIENT.get("/services/telegram-bots")
    assert "<details>" in detail.text
    assert "<summary>" in detail.text
