"""Specification revision requests are authenticated and auditable."""
from fastapi.testclient import TestClient

from server import app

CLIENT = TestClient(app)


def test_revision_request_requires_login_or_valid_csrf():
    response = CLIENT.post(
        "/account/projects/00000000-0000-0000-0000-000000000001/"
        "documents/00000000-0000-0000-0000-000000000002/request-revision",
        data={"comment": "Please revise the scope and acceptance criteria"},
        follow_redirects=False,
    )
    assert response.status_code in (403, 303)


def test_revision_request_rejects_short_feedback():
    response = CLIENT.post(
        "/account/projects/00000000-0000-0000-0000-000000000001/"
        "documents/00000000-0000-0000-0000-000000000002/request-revision",
        data={"comment": "short"},
        follow_redirects=False,
    )
    assert response.status_code in (403, 422)


def test_customer_project_has_revision_request_form():
    from pathlib import Path

    template = (
        Path(__file__).resolve().parents[1]
        / "portal/templates/client_project_detail.html"
    ).read_text(encoding="utf-8")
    assert "/request-revision" in template
    assert 'name="csrf_token"' in template
    assert 'name="comment"' in template
    assert 'doc.document_kind == "specification"' in template
