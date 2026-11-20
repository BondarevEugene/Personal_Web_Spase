"""Offline integrity check for an OMNIFACTORY project handover ZIP.

Usage: python scripts/verify_project_archive.py path/to/archive.zip
No external dependencies, database or network access required.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

SCHEMA = "omnifactory-project-archive-v1"
MAX_UNCOMPRESSED_BYTES = 4_000_000
MAX_FILES = 200


def verify_archive(path: str | Path) -> list[str]:
    errors: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if len(entries) > MAX_FILES or len(names) != len(set(names)):
                return ["Too many entries or duplicate filenames"]
            if any(
                name.startswith("/") or "\\" in name or ".." in name.split("/")
                or entry.is_dir()
                for name, entry in zip(names, entries, strict=True)
            ):
                return ["Unsafe ZIP path or directory entry"]
            if sum(entry.file_size for entry in entries) > MAX_UNCOMPRESSED_BYTES:
                return ["Archive exceeds uncompressed size limit"]
            if "manifest.json" not in names:
                return ["Missing manifest.json"]
            manifest = json.loads(archive.read("manifest.json"))
            if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
                return ["Unexpected archive schema"]
            expected = manifest.get("files")
            if not isinstance(expected, dict) or set(expected) != set(names) - {"manifest.json"}:
                return ["Manifest does not match archive entries"]
            for name, expected_hash in expected.items():
                if not isinstance(expected_hash, str) or len(expected_hash) != 64:
                    errors.append(f"Invalid checksum for {name}")
                    continue
                actual_hash = hashlib.sha256(archive.read(name)).hexdigest()
                if actual_hash != expected_hash:
                    errors.append(f"SHA-256 mismatch: {name}")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, RuntimeError) as exc:
        return [f"Unreadable archive: {exc}"]
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/verify_project_archive.py archive.zip")
        return 2
    errors = verify_archive(sys.argv[1])
    for error in errors:
        print("ERROR:", error)
    if errors:
        return 1
    print("OK: archive manifest and all file hashes verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
