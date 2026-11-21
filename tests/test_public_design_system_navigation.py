"""Public design system: one shared navigation and footer across the site."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server import app

ROOT = Path(__file__).resolve().parents[1]
CLIENT = TestClient(app)

PUBLIC_PAGES = (
    "/services", "/services/custom-crm", "/services/telegram-bots",
    "/services/business-automation", "/cases", "/cases/graph-studio",
    "/cases/client-workspace", "/cases/food-porn",
    "/cases/automation-studio", "/trust", "/trust/process",
    "/trust/security", "/trust/questions", "/journal",
    "/journal/graph-studio-python-export",
    "/journal/client-workspace-project-acceptance",
    "/journal/food-porn-telegram-digital-products",
    "/demo", "/demo/crm", "/demo/telegram", "/demo/automation",
)

NAV_LINKS = (
    "/", "/services", "/cases", "/demo",
    "/journal", "/trust", "/studio#contact",
)


@pytest.mark.parametrize("url", PUBLIC_PAGES)
def test_all_public_subpages_have_one_corporate_header_and_footer(url):
    response = CLIENT.get(url)
    assert response.status_code == 200, (url, response.text[:300])
    markup = response.text
    assert markup.count('class="journal-header omni-global-header"') == 1
    assert markup.count('class="journal-footer omni-global-footer"') == 1
    assert 'class="omni-mobile-menu"' in markup
    assert '<summary aria-label="Открыть навигацию">' in markup
    assert 'aria-label="Мобильная навигация"' in markup
    assert 'aria-label="Разделы сайта в подвале"' in markup
    assert '/studio-assets/public_shell.css?v=1' in markup
    assert 'href="#main"' in markup
    assert 'id="main"' in markup
    for href in NAV_LINKS:
        assert f'href="{href}"' in markup, (url, href)


@pytest.mark.parametrize("url,current", (
    ("/services", "/services"),
    ("/services/custom-crm", "/services"),
    ("/cases/graph-studio", "/cases"),
    ("/journal", "/journal"),
    ("/trust/security", "/trust"),
    ("/demo/telegram", "/demo"),
))
def test_current_section_is_announced_in_desktop_nav(url, current):
    markup = CLIENT.get(url).text
    assert f'href="{current}" aria-current="page"' in markup


def test_mobile_nav_is_native_and_does_not_need_custom_javascript():
    css_response = CLIENT.get("/studio-assets/public_shell.css")
    assert css_response.status_code == 200
    css = css_response.text
    assert "max-width:1160px" in css
    assert "max-width:540px" in css
    assert "focus-visible" in css
    assert "prefers-reduced-motion" in css
    header = (ROOT / "omni_site/templates/_public_header.html").read_text(
        encoding="utf-8",
    )
    assert "<details" in header and "<summary" in header
    assert "onclick=" not in header
    assert "<script" not in header
    assert 'href="/studio#contact"' in header
    assert header.count("<nav") == 2


def test_public_shell_does_not_change_authenticated_account_layout():
    markup = CLIENT.get("/account/login").text
    assert 'class="omni-mobile-menu"' not in markup
    assert 'class="journal-header omni-global-header"' not in markup


def test_public_homepage_keeps_original_navigation_and_interactive_lab():
    markup = CLIENT.get("/").text
    assert 'class="site-header"' in markup
    assert 'href="/demo"' in markup
    assert 'id="growth-calculator"' in markup
    assert 'class="journal-header omni-global-header"' not in markup
