"""Verify an offline OmniFactory Blueprint package without executing its content."""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from hashlib import sha256
from pathlib import Path


class PackageError(ValueError):
    """Malformed or corrupted Blueprint package."""


def verify_package(content: bytes) -> dict:
    if len(content) > 5_000_000:
        raise PackageError("Package exceeds 5 MB limit")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = archive.namelist()
            if len(names) > 32 or len(names) != len(set(names)):
                raise PackageError("Duplicate or excessive archive entries")
            if any(
                name.startswith("/") or ".." in Path(name).parts
                or "\\" in name or name.endswith("/")
                for name in names
            ):
                raise PackageError("Unsafe archive path")
            if "manifest.json" not in names:
                raise PackageError("Manifest missing")
            if any(item.file_size > 1_000_000 for item in archive.infolist()):
                raise PackageError("Archive entry exceeds size limit")
            manifest = json.loads(archive.read("manifest.json"))
            if manifest.get("schema") != "omnifactory.delivery.manifest.v1":
                raise PackageError("Unsupported manifest")
            files = manifest.get("files")
            if not isinstance(files, dict) or set(files) != set(names) - {"manifest.json"}:
                raise PackageError("Manifest file set mismatch")
            for name, expected in files.items():
                data = archive.read(name)
                if (
                    len(data) != expected.get("bytes")
                    or sha256(data).hexdigest() != expected.get("sha256")
                ):
                    raise PackageError(f"Checksum mismatch: {name}")
            blueprint = json.loads(archive.read("blueprint.json"))
            if blueprint.get("revision") != manifest.get("revision"):
                raise PackageError("Revision mismatch")
            if blueprint.get("deployable") is not False:
                raise PackageError("Blueprint is not executable")
            for name in (
                "architecture.json", "milestones.json",
                "verification.json", "risks.json",
            ):
                document = json.loads(archive.read(name))
                if document.get("revision") != manifest["revision"]:
                    raise PackageError(f"Revision mismatch: {name}")
            return {
                "ok": True,
                "revision": manifest["revision"],
                "files": len(files),
                "bytes": len(content),
            }
    except (zipfile.BadZipFile, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise PackageError("Invalid Blueprint package structure") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    args = parser.parse_args(argv)
    try:
        report = verify_package(args.package.read_bytes())
    except (PackageError, OSError) as exc:
        parser.exit(1, f"Blueprint package verification failed: {exc}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
