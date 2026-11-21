"""Guard the public Blueprint customer handoff against unsafe regressions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "omni_site" / "static"


def test_handoff_requires_explicit_click_and_same_origin_url():
    js = (ROOT / "blueprint_handoff.js").read_text(encoding="utf-8")
    assert 'button.addEventListener("click"' in js
    assert "safeProjectUrl(result.url)" in js
    assert 'value.startsWith("/account/")' in js
    assert "url.origin === window.location.origin" in js
    assert 'value.startsWith("//")' in js
    assert "link.href = target" in js


def test_handoff_and_graph_save_require_csrf_and_handle_expired_session():
    for file in ("blueprint_handoff.js", "blueprint_studio.js"):
        js = (ROOT / file).read_text(encoding="utf-8")
        assert 'credentials: "same-origin"' in js
        assert '"X-Omni-CSRF": token' in js
        assert "typeof token !== \"string\" || !token" in js
        assert "status === 401 ||" in js
        assert "status === 403" in js
        assert "disabled = true" in js
        assert "disabled = false" in js


def test_graph_save_validates_id_before_building_navigation():
    js = (ROOT / "blueprint_studio.js").read_text(encoding="utf-8")
    assert "typeof project.id !== \"string\"" in js
    assert "encodeURIComponent(project.id)" in js
    assert 'link.href = "/account/graph-project/"' in js
