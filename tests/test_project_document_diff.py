"""Version comparisons preserve content, order and tenant boundaries."""
from fastapi.testclient import TestClient

from portal.project_diff import compare_text
from server import app


def test_added_removed_and_unchanged_lines():
    rows = compare_text("first\nold\nlast", "first\nnew\nlast")
    assert [(row["kind"], row["text"]) for row in rows] == [
        ("same", "first"), ("removed", "old"),
        ("added", "new"), ("same", "last"),
    ]


def test_comparison_does_not_interpret_html():
    rows = compare_text("<script>alert(1)</script>", "<img src=x>")
    assert rows[0]["text"] == "<script>alert(1)</script>"
    assert rows[1]["text"] == "<img src=x>"


def test_anonymous_document_comparison_denied():
    response = TestClient(app).get(
        "/account/projects/00000000-0000-0000-0000-000000000001/"
        "documents/00000000-0000-0000-0000-000000000002/compare",
    )
    assert response.status_code == 401


def test_document_card_has_comparison_link():
    from pathlib import Path

    html = (
        Path(__file__).resolve().parents[1]
        / "portal/templates/client_project_detail.html"
    ).read_text(encoding="utf-8")
    assert "/compare" in html
    assert "doc.version > 1" in html
