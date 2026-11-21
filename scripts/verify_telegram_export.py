"""Offline acceptance check for a downloaded OMNIFACTORY Telegram bot ZIP.

Usage: python scripts/verify_telegram_export.py path/to/omnifactory_telegram_bot.zip
Does not read secrets or contact Telegram.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from api.export_contract import ExportContractError, verify_export_archive


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a Graph Studio bot ZIP")
    parser.add_argument("archive", type=Path, help="Path to generated ZIP")
    args = parser.parse_args()
    try:
        report = verify_export_archive(args.archive.read_bytes())
    except (OSError, ExportContractError) as exc:
        print(json.dumps({"verified": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
