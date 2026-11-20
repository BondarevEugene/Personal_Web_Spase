"""Public case journal: actual project sources, safe routing and conversion."""
from pathlib import Path

from fastapi.testclient import TestClient

from omni_site.editorial import ARTICLES, ARTICLE_BY_SLUG
from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_three_first_party_technical_articles_have_evidence_and_limitations():
    assert len(ARTICLES) == 3
    assert len(ARTICLE_BY_SLUG) == len(ARTICLES)
    for item in ARTICLES:
        assert item.source_url.startswith("https://github.com/BondarevEugene/")
        assert item.product_url.startswith("/")
        assert len(item.sections) >= 4
        assert all(len(section.body) >= 120 for section in item.sections)
        assert item.slug in ARTICLE_BY_SLUG
        response = CLIENT.get("/journal/" + item.slug)
        assert response.status_code == 200
        assert item.title in response.text
        assert item.sections[0].heading in response.text
        assert 'href="' + item.source_url + '"' in response.text
        assert 'href="/studio#contact"' in response.text
        assert 'name="description"' in response.text
        assert "О достоверности" in response.text


def test_journal_index_and_untrusted_slug_return_safe_results():
    response = CLIENT.get("/journal")
    assert response.status_code == 200
    for item in ARTICLES:
        assert 'href="/journal/' + item.slug + '"' in response.text
    assert "технические" in response.text.lower() or "инженерные" in response.text.lower()
    assert CLIENT.get("/journal/not-a-real-article").status_code == 404
    assert CLIENT.get("/journal/%3Cscript%3E").status_code == 404


def test_public_homepage_links_actual_journal_and_presets():
    response = CLIENT.get("/")
    assert response.status_code == 200
    for item in ARTICLES:
        assert 'href="/journal/' + item.slug + '"' in response.text
    assert 'href="/journal"' in response.text
    for preset in ("food", "crm", "bot"):
        assert 'data-growth-preset="' + preset + '"' in response.text
    assert "Иллюстративные сценарии" in response.text
    assert 'href="/studio#contact"' in response.text
    assert "не фактические показатели" in response.text


def test_articles_are_indexed_only_when_canonical_origin_is_configured(monkeypatch):
    monkeypatch.setenv("OMNI_PUBLIC_BASE_URL", "https://omni.example.com")
    response = CLIENT.get("/sitemap.xml")
    assert response.status_code == 200
    for item in ARTICLES:
        assert "https://omni.example.com/journal/" + item.slug in response.text
    monkeypatch.delenv("OMNI_PUBLIC_BASE_URL", raising=False)
    assert CLIENT.get("/sitemap.xml").status_code == 404


def test_journal_layout_and_frontend_presets_are_lightweight():
    css = CLIENT.get("/studio-assets/journal.css")
    assert css.status_code == 200
    assert "max-width:650px" in css.text
    source = (ROOT / "omni_site/static/public_growth.js").read_text(
        encoding="utf-8"
    )
    assert "data-growth-preset" in source
    assert "Hypothetical starting inputs" in source
    assert "fetch(" not in source
    assert "localStorage" not in source
