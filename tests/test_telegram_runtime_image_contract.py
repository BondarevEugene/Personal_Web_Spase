"""Regression tests for Telegram runtime production image packaging."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime" / "telegram"


def test_production_dockerfile_packages_every_runtime_import():
    dockerfile = (RUNTIME / "Dockerfile").read_text(encoding="utf-8")
    for module in ("app.py", "scenario.py", "state.py", "maintenance.py"):
        assert (RUNTIME / module).is_file()
        assert f"COPY runtime/telegram/{module} /app/{module}" in dockerfile


def test_runtime_imports_and_single_replica_lock_are_packaged():
    app = (RUNTIME / "app.py").read_text(encoding="utf-8")
    assert "from state import DialogueStore" in app
    assert "conversation_locks.setdefault(key, asyncio.Lock())" in app
    assert "async with lock:" in app


def test_runtime_image_owns_persistent_directory():
    dockerfile = (RUNTIME / "Dockerfile").read_text(encoding="utf-8")
    assert "chown 10001:10001 /data" in dockerfile
    assert "USER 10001" in dockerfile
