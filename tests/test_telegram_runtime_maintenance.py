from runtime.telegram.maintenance import maintain
from runtime.telegram.state import DialogueStore


def test_statistics_and_integrity_do_not_expose_dialogue_text(tmp_path):
    path = str(tmp_path / "state.db")
    store = DialogueStore(path)
    store.write((100, 200), "waiting", {"secret": "private text"})
    assert store.claim_update(5)
    assert store.check() is True
    assert store.statistics() == {
        "dialogues": 1, "waiting": 1, "processed_updates": 1,
    }
    store.close()
    report = maintain(path, retention_days=30)
    assert report["database_healthy"] is True
    assert "private text" not in str(report)
    assert report["applied"] is False


def test_maintenance_rejects_bad_retention_and_missing_file(tmp_path):
    path = str(tmp_path / "missing.db")
    import pytest
    with pytest.raises(ValueError):
        maintain(path, retention_days=0)
    with pytest.raises(FileNotFoundError):
        maintain(path, retention_days=30)
