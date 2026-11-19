"""Regression checks for the customer service desk's route and schema contracts."""
from pathlib import Path

from portal.models import SupportMessage, SupportTicket
from portal.routes import router


def test_support_routes_are_registered():
    paths = {(route.path, method) for route in router.routes
             for method in getattr(route, "methods", set())}
    assert ("/account/tickets", "GET") in paths
    assert ("/account/tickets", "POST") in paths
    assert ("/account/tickets/{ticket_id}", "GET") in paths
    assert ("/account/tickets/{ticket_id}/messages", "POST") in paths


def test_support_entities_have_org_boundary_and_audit_fields():
    tickets = SupportTicket.__table__.columns
    messages = SupportMessage.__table__.columns
    for field in ("org_id", "created_by_id", "status", "updated_at"):
        assert field in tickets
    for field in ("ticket_id", "author_id", "created_at"):
        assert field in messages


def test_support_pages_keep_csrf_and_workflow_entry_points():
    folder = Path(__file__).resolve().parents[1] / "portal" / "templates"
    ticket_list = (folder / "tickets.html").read_text(encoding="utf-8")
    ticket_detail = (folder / "ticket_detail.html").read_text(encoding="utf-8")
    dashboard = (folder / "dashboard.html").read_text(encoding="utf-8")
    assert 'name="csrf_token"' in ticket_list
    assert 'name="csrf_token"' in ticket_detail
    assert 'action="/account/tickets"' in ticket_list
    assert "/account/tickets" in dashboard
    assert 'name="body"' in ticket_detail
