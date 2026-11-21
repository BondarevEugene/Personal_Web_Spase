"""Graph Studio exposes the saved-project release workflow to customers."""
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "builder_pro_final.html"


def test_release_workflow_controls_exist():
    html = TEMPLATE.read_text(encoding="utf-8")
    for token in (
        'id="builder-release-workflow"',
        'id="btn-workflow-check"',
        'id="builder-workflow-stages"',
        'id="builder-workflow-errors"',
        'id="builder-workflow-export"',
    ):
        assert token in html


def test_workflow_reads_saved_project_and_displays_preflight():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "'/workflow'" in html
    assert "report.preflight?.issues" in html
    assert "report.export_available" in html
    assert "select.addEventListener('change', reset)" in html
    assert "textContent = issue.node_id" in html


def test_workflow_does_not_promise_live_deployment():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert "Публикация в Railway пока выполняется вручную" in html
