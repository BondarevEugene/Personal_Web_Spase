"""Customer project overview regression contracts.

No external services or production database needed.
"""
from pathlib import Path

from portal.models import AutomationWorkflow, BuilderProject


ROOT = Path(__file__).resolve().parents[1]


def test_project_models_are_owned_by_individual_customer():
    assert "customer_id" in BuilderProject.__table__.columns
    assert "customer_id" in AutomationWorkflow.__table__.columns


def test_dashboard_queries_are_scoped_to_current_customer():
    code = (ROOT / "portal" / "routes.py").read_text(encoding="utf-8")
    assert "BuilderProject.customer_id == user.id" in code
    assert "AutomationWorkflow.customer_id == user.id" in code
    assert "SupportTicket.org_id == user.org_id" in code
    assert "SupportTicket.status.notin_" in code


def test_dashboard_labels_saved_objects_truthfully():
    html = (ROOT / "portal" / "templates" / "dashboard.html").read_text(encoding="utf-8")
    assert "{{ bot_count }}" in html
    assert "{{ flow_count }}" in html
    assert "{{ active_ticket_count }}" in html
    assert "Черновик" in html
    assert "не считаются работающими ботами" in html
    assert 'href="/architect"' in html
    assert 'href="/automation/studio"' in html
    assert "support_statuses.get" in html


def test_client_project_panels_are_accessible_on_mobile():
    css = (ROOT / "omni_site" / "static" / "account.css").read_text(encoding="utf-8")
    assert ".account-project-grid" in css
    assert "@media(max-width:830px)" in css
