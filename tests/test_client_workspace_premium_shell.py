"""Regression contracts for the premium Client Workspace shell.

These tests protect server-backed navigation, forms, and accessible focus states.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_workspace_navigation_preserves_all_customer_routes():
    html = (ROOT / "portal/templates/_workspace_nav.html").read_text(encoding="utf-8")
    for route in (
        "/account", "/account/workspace", "/account/projects",
        "/account/decisions", "/account/notifications", "/account/tickets",
        "/account/finance", "/account/billing", "/account/security",
        "/architect", "/automation/studio",
    ):
        assert f'href="{route}"' in html
    assert 'action="/account/language"' in html
    assert 'name="csrf_token"' in html
    assert 'aria-current="page"' in html
    assert 'workspace-nav-caption' in html


def test_premium_shell_is_loaded_after_legacy_styles():
    page = (ROOT / "portal/templates/client_project_detail.html").read_text(
        encoding="utf-8"
    )
    assert page.index("account.css") < page.index("client_workspace.css")
    assert '{% include "_workspace_nav.html" %}' in page
    for endpoint in ("/attachments", "/documents/", "/messages", "/accept"):
        assert endpoint in page


def test_premium_css_has_accessibility_and_mobile_contracts():
    css = (ROOT / "omni_site/static/client_workspace.css").read_text(
        encoding="utf-8"
    )
    for token in (
        "--cw-bg", "--cw-surface", "--cw-border",
        ".workspace-nav-caption", ":focus-visible",
        "@media(max-width:850px)", "prefers-reduced-motion",
    ):
        assert token in css
    assert "box-shadow:none" in css
