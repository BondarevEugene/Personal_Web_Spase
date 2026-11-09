"""Local onboarding regression tests; no external Neon/Telegram access required."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from portal import db
from portal.bootstrap import PortalSchemaNotReady, ensure_portal_database, portal_schema_status, ui_source_status
from server import app


@pytest.fixture()
def clear_portal_caches():
    db.engine.cache_clear()
    db.session_factory.cache_clear()
    yield
    db.engine().dispose()
    db.engine.cache_clear()
    db.session_factory.cache_clear()


def test_local_default_sqlite_migrates_on_first_boot(tmp_path, monkeypatch, clear_portal_caches):
    monkeypatch.setattr(db, "ROOT", tmp_path)
    monkeypatch.delenv("OMNI_PORTAL_DATABASE_URL", raising=False)
    monkeypatch.delenv("OMNI_PORTAL_MIGRATION_URL", raising=False)
    monkeypatch.delenv("OMNI_PORTAL_DEV_AUTO_MIGRATE", raising=False)
    ensure_portal_database()
    ready, revision, expected = portal_schema_status()
    assert ready and revision == expected == "20261109_portal_02"
    assert (tmp_path / "portal_dev.sqlite3").exists()
    with db.engine().connect() as connection:
        assert "portal_customers" in inspect(connection).get_table_names()
        assert "portal_plans" in inspect(connection).get_table_names()
    # Safe to call more than once; a second launch does not reset data.
    ensure_portal_database()


def test_explicit_database_never_auto_migrates_unless_development_opt_in(
    tmp_path, monkeypatch, clear_portal_caches
):
    db_file = tmp_path / "external.sqlite3"
    monkeypatch.setenv("OMNI_PORTAL_DATABASE_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.setenv("OMNI_PORTAL_MIGRATION_URL", f"sqlite:///{db_file.as_posix()}")
    monkeypatch.delenv("OMNI_PORTAL_DEV_AUTO_MIGRATE", raising=False)
    with pytest.raises(PortalSchemaNotReady, match="upgrade head"):
        ensure_portal_database()
    assert portal_schema_status()[0] is False
    monkeypatch.setenv("OMNI_PORTAL_DEV_AUTO_MIGRATE", "1")
    ensure_portal_database()
    assert portal_schema_status()[0] is True


def test_root_source_is_studio_v3_and_has_build_header():
    html_path, version_ok = ui_source_status()
    assert html_path.endswith("index.html")
    assert version_ok
    r = TestClient(app).get("/?ui=20261109")
    assert r.status_code == 200
    assert r.headers["x-omni-ui"] == "studio-v3-platform"
    assert "platform-app" in r.text
    assert "EVO MASTER" not in r.text
