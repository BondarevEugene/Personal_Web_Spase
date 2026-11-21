"""SQLite runtime state backup, verification and offline restore.

All operations are local and never transmit state, tokens or user messages.
Backups contain sensitive conversation variables; store them encrypted at rest
with restricted operator access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError("SQLite database does not exist")
    connection = sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    try:
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise sqlite3.DatabaseError("SQLite integrity check failed")
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"dialogues", "updates"}.issubset(tables):
            raise sqlite3.DatabaseError("Not an OmniFactory dialogue database")
        return {
            "healthy": True,
            "dialogues": connection.execute(
                "SELECT count(*) FROM dialogues").fetchone()[0],
            "updates": connection.execute(
                "SELECT count(*) FROM updates").fetchone()[0],
            "sha256": checksum(path),
        }
    finally:
        connection.close()


def backup(source: Path, destination: Path) -> dict:
    """Consistent snapshot via SQLite online backup API, atomic destination."""
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise ValueError("Source and destination must differ")
    if destination.exists():
        raise FileExistsError("Backup destination already exists")
    if not destination.parent.is_dir():
        raise FileNotFoundError("Backup destination directory does not exist")
    inspect(source)
    fd, temp_name = tempfile.mkstemp(prefix=".omni-backup-", suffix=".sqlite",
                                     dir=destination.parent)
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as reader:
            with sqlite3.connect(temporary) as writer:
                reader.backup(writer)
        result = inspect(temporary)
        os.chmod(temporary, 0o600)
        if destination.exists():
            raise FileExistsError("Backup destination already exists")
        temporary.rename(destination)
        return {"path": str(destination), **result}
    finally:
        temporary.unlink(missing_ok=True)


def restore(source: Path, destination: Path, *, expected_sha256: str) -> dict:
    """Restore only to an absent destination; runtime MUST be stopped.

    Replacing an existing database while a process is using SQLite is unsafe,
    so operators must move the old file out of the way offline first.
    """
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise ValueError("Source and destination must differ")
    if destination.exists() or not destination.parent.is_dir():
        raise FileExistsError("Restore destination must be absent in an existing directory")
    verified = inspect(source)
    if verified["sha256"] != expected_sha256:
        raise ValueError("Backup checksum mismatch")
    return backup(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="OmniFactory runtime SQLite recovery")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("verify")
    check.add_argument("source", type=Path)
    save = sub.add_parser("backup")
    save.add_argument("source", type=Path)
    save.add_argument("destination", type=Path)
    recover = sub.add_parser("restore")
    recover.add_argument("source", type=Path)
    recover.add_argument("destination", type=Path)
    recover.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if args.command == "verify":
        result = inspect(args.source)
    elif args.command == "backup":
        result = backup(args.source, args.destination)
    else:
        result = restore(args.source, args.destination, expected_sha256=args.sha256)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
