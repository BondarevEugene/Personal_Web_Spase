"""Keep Chromium audit expectations aligned with actual Blueprint architecture."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_blueprint_architecture_panels_and_audit_agree():
    html = (ROOT / "omni_site/templates/blueprint_studio.html").read_text(
        encoding="utf-8"
    )
    audit = (ROOT / "scripts/public_ux_audit.py").read_text(
        encoding="utf-8"
    )
    assert html.count('class="blueprint-block') == 4
    for label in (
        "Модули архитектуры",
        "Этапы реализации",
        "Критерии приёмки",
        "Риски и ограничения",
    ):
        assert label in html
    selector = '".blueprint-content-grid .blueprint-block"'
    assert selector in audit
    assert ").count() != 4:" in audit[audit.index(selector):][:120]
