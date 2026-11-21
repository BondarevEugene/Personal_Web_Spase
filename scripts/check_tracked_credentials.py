"""Fail CI if tracked files contain Google/Firebase service-account credentials.

Only tracked files are inspected; no private developer files or secrets are printed.
Historical commits and credential revocation require a separate security review.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = ("firebase-adminsdk", "service-account", "service_account")
KEY_FIELDS = {"private_key", "private_key_id", "client_email"}
ACCOUNT_TYPE = "service_account"


def tracked_files(root: Path = ROOT) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def violations(root: Path = ROOT, paths: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    for name in paths if paths is not None else tracked_files(root):
        path = root / name
        if not path.is_file():
            continue
        lowered = path.name.lower()
        if path.suffix.lower() != ".json":
            continue
        if any(fragment in lowered for fragment in FORBIDDEN_NAMES):
            errors.append(f"{name}: forbidden credential filename")
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeError, ValueError):
            continue
        if isinstance(document, dict) and (
            document.get("type") == ACCOUNT_TYPE
            and KEY_FIELDS.issubset(document)
        ):
            errors.append(f"{name}: tracked service-account credential")
    return errors


def main() -> int:
    errors = violations()
    for error in errors:
        print(error)
    if errors:
        print("Credential hygiene failed: revoke exposed keys and remove tracked credentials.")
        return 1
    print("Tracked JSON credential hygiene: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
