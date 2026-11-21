"""Guard restored CI coverage against accidental branch drift or missing suites."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
BASE = "feat/graph-runtime-incident-triage-20261121"


def test_recovered_gate_has_all_critical_regressions():
    workflow = (WORKFLOWS / "recovered_feature_gates.yml").read_text(encoding="utf-8")
    for name in (
        "test_automation_connections.py",
        "test_connection_vault.py",
        "test_connection_health.py",
        "test_automation_oauth.py",
        "test_automation_control_center.py",
        "test_telegram_runtime_production.py",
        "test_telegram_outbox.py",
        "test_project_delivery_approval_gate.py",
    ):
        assert name in workflow
        assert (ROOT / "tests" / name).is_file()
    assert BASE in workflow
    assert "workflow_dispatch:" in workflow


def test_public_and_workspace_gates_target_active_branch():
    for name in ("client_workspace_quality.yml", "public_browser_quality.yml"):
        content = (WORKFLOWS / name).read_text(encoding="utf-8")
        assert BASE in content
        assert "feat/founders-omni-editorial-20261116" not in content


def test_public_gate_covers_combined_css_build():
    content = (WORKFLOWS / "public_browser_quality.yml").read_text(encoding="utf-8")
    assert "build_home_page_css.py" in content
    assert (ROOT / "scripts" / "build_home_page_css.py").is_file()
