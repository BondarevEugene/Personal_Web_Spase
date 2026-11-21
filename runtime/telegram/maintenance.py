"""Operational maintenance for a single-replica Telegram runtime SQLite volume.

Run with the webhook worker stopped to avoid contention during VACUUM.
No bot token, user text, or chat identifiers are printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path

try:
    from .state import DialogueStore
except ImportError:
    from state import DialogueStore


def maintain(path: str, *, retention_days: int, apply: bool = False) -> dict:
    if not 1 <= retention_days <= 365:
        raise ValueError("Retention must be between 1 and 365 days")
    if not Path(path).is_file():
        raise FileNotFoundError("Runtime state file does not exist")
    store = DialogueStore(path)
    try:
        before = store.statistics()
        healthy = store.check()
        if not healthy:
            raise sqlite3.DatabaseError("SQLite quick_check failed")
        if apply:
            store.prune(retention_days * 86400)
        after = store.statistics()
        return {
            "database_healthy": healthy,
            "retention_days": retention_days,
            "applied": apply,
            "before": before, "after": after,
        }
    finally:
        store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Telegram runtime state maintenance")
    parser.add_argument("--path", default=os.getenv("OMNI_STATE_SQLITE_PATH"))
    parser.add_argument("--retention-days", type=int, default=30)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.path:
        parser.error("--path or OMNI_STATE_SQLITE_PATH is required")
    print(json.dumps(maintain(args.path, retention_days=args.retention_days,
                              apply=args.apply), ensure_ascii=False))


if __name__ == "__main__":
    main()
