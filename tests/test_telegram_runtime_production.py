"""Crash-recovery receipts and production configuration tests."""
import base64
import json
import sqlite3
import time

import pytest

from runtime.telegram.state import DialogueStore


def test_receipt_completes_and_survives_restart(tmp_path):
    path = str(tmp_path / "receipts.sqlite3")
    first = DialogueStore(path)
    assert first.claim_update(17)
    assert not first.claim_update(17)
    first.complete_update(17)
    first.close()
    second = DialogueStore(path)
    assert not second.claim_update(17, lease_seconds=0)
    second.close()


def test_abandoned_receipt_can_be_reclaimed(tmp_path):
    path = str(tmp_path / "receipts.sqlite3")
    store = DialogueStore(path)
    assert store.claim_update(18)
    assert not store.claim_update(18)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE updates SET created_at=? WHERE update_id=?",
                   (int(time.time()) - 3600, 18))
    assert store.claim_update(18, lease_seconds=300)
    assert not store.claim_update(18)
    store.close()


def test_legacy_receipts_are_not_replayed(tmp_path):
    path = str(tmp_path / "legacy.sqlite3")
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE updates (update_id INTEGER PRIMARY KEY, created_at INTEGER NOT NULL)")
        db.execute("INSERT INTO updates VALUES (99, 1)")
    store = DialogueStore(path)
    assert not store.claim_update(99, lease_seconds=0)
    assert store.claim_update(100)
    store.close()


def test_production_requires_persistent_absolute_path(monkeypatch):
    from runtime.telegram import app as runtime
    monkeypatch.setenv("BOT_TOKEN", "123456789:" + "A" * 35)
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "A" * 40)
    spec = {"name": "Test", "start": "end",
            "nodes": [{"id": "end", "kind": "end", "text": "Done"}]}
    monkeypatch.setenv("OMNI_SCENARIO_BASE64",
                       base64.b64encode(json.dumps(spec).encode()).decode())
    monkeypatch.setenv("OMNI_RUNTIME_PRODUCTION", "1")
    monkeypatch.delenv("OMNI_STATE_SQLITE_PATH", raising=False)
    with pytest.raises(RuntimeError, match="absolute persistent"):
        runtime.load_app()
    monkeypatch.setenv("OMNI_STATE_SQLITE_PATH", "relative/state.sqlite3")
    with pytest.raises(RuntimeError, match="absolute persistent"):
        runtime.load_app()
