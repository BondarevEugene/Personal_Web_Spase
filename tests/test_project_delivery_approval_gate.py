"""Regression checks for latest delivery approval as a final acceptance gate."""
from inspect import getsource
from pathlib import Path

from portal.client_projects import accept_project
from portal.project_documents import approve_document


def test_acceptance_requires_current_delivery_acknowledgement():
    source = getsource(accept_project)
    assert 'ClientProjectDocument.document_kind == "delivery"' in source
    assert "ClientProjectApproval.document_id == latest_delivery" in source
    assert "ClientProjectApproval.org_id == user.org_id" in source
    assert "Сначала согласуйте последнюю редакцию" in source
    assert source.index("delivery_approval is None") < source.index(
        'project.status, project.updated_at = "accepted"'
    )


def test_approval_endpoint_rejects_obsolete_revisions():
    source = getsource(approve_document)
    assert "doc.version != latest" in source
    assert "Согласовать можно только последнюю версию" in source
    assert 'user.role != "owner"' in source


def test_customer_acceptance_ui_explains_prerequisite():
    html = (
        Path(__file__).resolve().parents[1]
        / "portal/templates/client_project_detail.html"
    ).read_text(encoding="utf-8")
    assert "Перед окончательной приёмкой" in html
    assert "Описание результата" in html
    assert 'action="/account/projects/{{ project.id }}/accept"' in html
