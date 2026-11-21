"""OMNIFACTORY Visual Excellence: first impression and mobile conversion."""
from pathlib import Path

from fastapi.testclient import TestClient

from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)


def test_homepage_has_single_clear_hero_and_three_real_routes():
    response = CLIENT.get("/")
    assert response.status_code == 200
    markup = response.text
    assert markup.count("<h1>") == 1
    assert "Ваш бизнес." in markup
    assert 'href="/studio#contact"' in markup
    assert 'class="omni-hero-pathways"' in markup
    assert 'aria-label="Быстрый выбор направления"' in markup
    assert 'href="/services"' in markup
    assert 'href="/cases"' in markup
    assert 'href="/demo"' in markup
    assert 'class="omni-proof-strip"' in markup
    assert "Собственный Python-код" in markup
    assert "Проверяемые сценарии" in markup
    assert "Прозрачные ограничения" in markup


def test_rail_contains_only_six_distinct_onpage_targets():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    rail = html.split('<nav class="omni-section-rail"', 1)[1].split(
        "</nav>", 1,
    )[0]
    assert rail.count("<a ") == 6
    assert 'href="/trust"' not in rail
    assert 'href="/demo"' not in rail
    targets = (
        "workspace", "products", "benefit", "journal", "founders", "status",
    )
    for name in targets:
        assert rail.count(f'href="#{name}"') == 1
        assert f'id="{name}"' in html


def test_main_headline_stays_stable_for_existing_cms():
    from omni_site.creative_store import HOME_HERO_ORIGINAL, HOME_SUMMARY_ORIGINAL
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert HOME_HERO_ORIGINAL in html
    assert HOME_SUMMARY_ORIGINAL in html
    assert html.count(HOME_HERO_ORIGINAL) == 1


def test_mobile_contact_is_real_and_respects_safe_areas():
    html = CLIENT.get("/").text
    assert 'class="omni-mobile-contact"' in html
    assert 'aria-label="Обсудить проект с OMNIFACTORY"' in html
    assert 'href="/studio#contact"' in html
    css_response = CLIENT.get("/studio-assets/visual_excellence.css")
    assert css_response.status_code == 200
    css = css_response.text
    for selector in (
        ".omni-mobile-contact", ".omni-hero-pathways",
        ".omni-proof-inner", "prefers-reduced-motion",
        "max-width:690px", "max-width:430px", "focus-visible",
    ):
        assert selector in css
    assert "env(safe-area-inset-bottom)" in css


def test_excellence_does_not_add_javascript_or_fake_results():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert 'home_page.bundle.css?v=1' in html
    assert 'visual_excellence.js' not in html
    assert 'https://fonts.googleapis.com' in html
    assert 'https://fonts.gstatic.com' in html
    assert "500 000 клиентов" not in html
    assert "99.9% удовлетворённости" not in html
    assert "проверяемые" in html.lower()
    assert CLIENT.get("/services").status_code == 200
    assert CLIENT.get("/cases").status_code == 200
    assert CLIENT.get("/demo").status_code == 200
    assert CLIENT.get("/trust").status_code == 200


def test_account_layout_is_unaffected():
    login = CLIENT.get("/account/login")
    assert login.status_code == 200
    assert 'class="omni-mobile-contact"' not in login.text
    assert 'visual_excellence.css' not in login.text
