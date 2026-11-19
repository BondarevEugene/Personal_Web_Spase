"""Static regression checks for Unified Experience shell.

No browser or database required; this catches nav drift and malformed cabinet KPIs.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "index.html",
    "templates/builder_pro_final.html",
    "templates/cloud_deploy.html",
    "templates/automation_studio.html",
    "templates/bot_lab.html",
    "portal/templates/auth.html",
    "portal/templates/dashboard.html",
    "portal/templates/billing.html",
    "portal/templates/tickets.html",
    "portal/templates/ticket_detail.html",
    "portal/templates/support_operator_queue.html",
    "portal/templates/support_operator_detail.html",
)


def _html(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_all_primary_pages_load_unified_shell():
    for page in PAGES:
        content = _html(page)
        assert "/studio-assets/unified_shell.css?v=1" in content, page
        assert content.count("unified_shell.css") == 1, page


def test_home_uses_top_level_routes_and_right_section_navigation():
    page = _html("index.html")
    top = page.split('<nav id="main-nav"', 1)[1].split("</nav>", 1)[0]
    assert 'href="#founders"' not in top
    for href in ("/architect", "/cloud/deploy", "/automation/studio", "/account"):
        assert f'href="{href}"' in top
    aside = page.split('class="omni-section-rail"', 1)[1].split("</nav>", 1)[0]
    for target in ("workspace", "products", "founders", "status"):
        assert f'href="#{target}"' in aside
        assert re.search(r'id="' + target + r'"', page)
    assert 'id="omni-idea-next"' in page
    assert "/studio-assets/unified_shell.js?v=1" in page


def test_customer_dashboard_kpis_have_balanced_article_tags():
    page = _html("portal/templates/dashboard.html")
    kpis = page.split('<div class="account-kpis">', 1)[1].split("</div>", 1)[0]
    assert kpis.count("<article>") == kpis.count("</article>")
    assert '<span>ТЕКУЩИЙ ПЛАН</span>' in kpis
    assert 'href="/account/tickets"' in page
    assert 'class="account-section-nav"' in page


def test_legacy_tool_pages_share_module_links():
    for name in ("cloud_deploy", "automation_studio", "bot_lab"):
        page = _html(f"templates/{name}.html")
        header = page.split('<nav class="omni-nav"', 1)[1].split("</nav>", 1)[0]
        for route in ("/", "/architect", "/bots/lab", "/automation/studio",
                      "/cloud/deploy", "/account"):
            assert f'href="{route}"' in header, (name, route)
