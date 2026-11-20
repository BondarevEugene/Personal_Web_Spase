"""SQLite state backup and recovery integration tests."""
import hashlib
import sqlite3

import pytest

from runtime.telegram.backup import backup, inspect, restore
from runtime.telegram.state import DialogueStore


def test_consistent_backup_restore_preserves_cursor_and_dedup(tmp_path):
    source = tmp_path / "live.db"
    store = DialogueStore(str(source))
    store.write((123, 456), "ask_name", {"name": "Тест"})
    assert store.claim_update(500)
    backup_path = tmp_path / "snapshot.db"
    result = backup(source, backup_path)
    assert result["healthy"]
    assert result["dialogues"] == 1
    assert result["updates"] == 1
    assert len(result["sha256"]) == 64
    assert store.claim_update(501)
    store.close()

    restored = tmp_path / "restored.db"
    recovery = restore(backup_path, restored, expected_sha256=result["sha256"])
    assert recovery["healthy"]
    recovered_store = DialogueStore(str(restored))
    assert recovered_store.read((123, 456)) == ("ask_name", {"name": "Тест"})
    assert not recovered_store.claim_update(500)
    assert recovered_store.claim_update(501)
    recovered_store.close()


def test_refuses_overwrite_and_wrong_checksum(tmp_path):
    source = tmp_path / "live.db"
    store = DialogueStore(str(source))
    store.close()
    destination = tmp_path / "snapshot.db"
    backup(source, destination)
    with pytest.raises(FileExistsError):
        backup(source, destination)
    with pytest.raises(ValueError, match="checksum"):
        restore(destination, tmp_path / "restore.db", expected_sha256="0" * 64)
    assert not (tmp_path / "restore.db").exists()


def test_refuses_unrelated_sqlite_database(tmp_path):
    other = tmp_path / "other.db"
    with sqlite3.connect(other) as connection:
        connection.execute("CREATE TABLE unrelated (id INTEGER)")
    with pytest.raises(sqlite3.DatabaseError):
        inspect(other)


def test_refuses_same_source_and_destination(tmp_path):
    source = tmp_path / "live.db"
    store = DialogueStore(str(source))
    store.close()
    with pytest.raises(ValueError):
        backup(source, source)
