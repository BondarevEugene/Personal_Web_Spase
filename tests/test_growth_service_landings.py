"""Public service landing catalogue and SEO coverage."""

from omni_site.services_catalog import SERVICES, SERVICE_BY_SLUG
from omni_site.search_discovery import sitemap


def test_four_service_landings_have_unique_slugs_and_complete_content():
    assert len(SERVICES) == 4
    assert len(SERVICE_BY_SLUG) == len(SERVICES)
    assert {item.slug for item in SERVICES} == {
        "custom-crm", "telegram-bots", "business-automation", "ai-solutions",
    }
    for item in SERVICES:
        assert item.title and item.summary and item.audience
        assert item.deliverables and item.process and item.limitations
        assert item.questions and item.stack
        assert item.case_url.startswith("/cases/")
        assert item.journal_url.startswith("/journal/")
        assert item.lead_topic


def test_all_service_landing_urls_appear_once_in_sitemap(monkeypatch):
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omnifactory.example")
    body = sitemap().body.decode("utf-8")
    for service in SERVICES:
        url = f"https://omnifactory.example/services/{service.slug}"
        assert body.count(f"<loc>{url}</loc>") == 1


def test_ai_service_explains_quality_privacy_and_cost_boundaries():
    service = SERVICE_BY_SLUG["ai-solutions"]
    limitations = " ".join(service.limitations).lower()
    assert "ошиб" in limitations
    assert "данн" in limitations
    assert "стоимость" in limitations
