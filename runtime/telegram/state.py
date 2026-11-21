"""SQLite-backed single-replica Telegram dialogue state and update replay guard.

The SQLite file MUST reside on persistent storage. For multiple replicas use a
transactional shared database and distributed lock instead of this adapter.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path


class DialogueStore:
    def __init__(self, filename: str):
        if not filename:
            raise ValueError("Persistent SQLite path required")
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(filename, check_same_thread=False, timeout=15)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA busy_timeout=15000")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS dialogues (
            chat_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
            cursor TEXT, variables TEXT NOT NULL DEFAULT '{}',
            updated_at INTEGER NOT NULL,
            PRIMARY KEY(chat_id, user_id))""")
        self.connection.execute("""CREATE TABLE IF NOT EXISTS updates (
            update_id INTEGER PRIMARY KEY, created_at INTEGER NOT NULL)""")
        # Add receipt state without dropping legacy update IDs on upgrade.
        columns = {row[1] for row in self.connection.execute(
            "PRAGMA table_info(updates)").fetchall()}
        if "status" not in columns:
            self.connection.execute(
                "ALTER TABLE updates ADD COLUMN status TEXT NOT NULL DEFAULT 'done'")
        self.connection.commit()
        self.lock = threading.RLock()

    def read(self, key: tuple[int, int]) -> tuple[str | None, dict[str, str]]:
        with self.lock:
            row = self.connection.execute(
                "SELECT cursor, variables FROM dialogues WHERE chat_id=? AND user_id=?",
                key).fetchone()
            if row is None:
                return None, {}
            return row[0], json.loads(row[1])

    def write(self, key: tuple[int, int], cursor: str | None, variables: dict[str, str]):
        with self.lock:
            self.connection.execute(
                """INSERT INTO dialogues(chat_id,user_id,cursor,variables,updated_at)
                VALUES(?,?,?,?,?) ON CONFLICT(chat_id,user_id) DO UPDATE SET
                cursor=excluded.cursor,variables=excluded.variables,
                updated_at=excluded.updated_at""",
                (*key, cursor, json.dumps(variables, ensure_ascii=False), int(time.time())))
            self.connection.commit()

    def clear(self, key: tuple[int, int]):
        with self.lock:
            self.connection.execute(
                "DELETE FROM dialogues WHERE chat_id=? AND user_id=?", key)
            self.connection.commit()

    def claim_update(self, update_id: int, lease_seconds: int = 300) -> bool:
        """Claim an update, or reclaim a processing receipt abandoned by a crash.

        Completed receipts are not reclaimed before retention pruning.
        Single-replica only.
        """
        now = int(time.time())
        with self.lock:
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                row = self.connection.execute(
                    "SELECT status, created_at FROM updates WHERE update_id=?",
                    (update_id,),
                ).fetchone()
                if row is None:
                    self.connection.execute(
                        "INSERT INTO updates(update_id,created_at,status) "
                        "VALUES(?,?,'processing')", (update_id, now))
                    claimed = True
                elif row[0] == "processing" and row[1] <= now - lease_seconds:
                    self.connection.execute(
                        "UPDATE updates SET created_at=? WHERE update_id=?",
                        (now, update_id))
                    claimed = True
                else:
                    claimed = False
                self.connection.commit()
                return claimed
            except Exception:
                self.connection.rollback()
                raise

    def complete_update(self, update_id: int) -> None:
        """Mark successfully dispatched update as deduplicated."""
        with self.lock:
            self.connection.execute(
                "UPDATE updates SET status='done',created_at=? WHERE update_id=?",
                (int(time.time()), update_id))
            self.connection.commit()

    def forget_update(self, update_id: int):
        with self.lock:
            self.connection.execute("DELETE FROM updates WHERE update_id=?", (update_id,))
            self.connection.commit()

    def prune(self, max_age_seconds: int = 604800):
        threshold = int(time.time()) - max_age_seconds
        with self.lock:
            self.connection.execute("DELETE FROM updates WHERE created_at < ?", (threshold,))
            self.connection.execute("DELETE FROM dialogues WHERE updated_at < ?", (threshold,))
            self.connection.commit()

    def statistics(self) -> dict[str, int]:
        """Aggregate counters without user identifiers or message text."""
        with self.lock:
            dialogues = self.connection.execute(
                "SELECT count(*) FROM dialogues").fetchone()[0]
            updates = self.connection.execute(
                "SELECT count(*) FROM updates").fetchone()[0]
            waiting = self.connection.execute(
                "SELECT count(*) FROM dialogues WHERE cursor IS NOT NULL").fetchone()[0]
            return {"dialogues": dialogues, "waiting": waiting,
                    "processed_updates": updates}

    def check(self) -> bool:
        """Verify SQLite integrity; not a Telegram delivery check."""
        with self.lock:
            return self.connection.execute("PRAGMA quick_check").fetchone()[0] == "ok"

    def close(self):
        with self.lock:
            self.connection.close()
