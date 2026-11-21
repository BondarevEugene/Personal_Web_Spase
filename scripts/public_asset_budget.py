"""Read-only inventory of public CSS and JS served by the FastAPI app.

It measures actual response bodies from the app's public routes and flags
broken static assets. Numbers are bundle bytes, not Lighthouse scores.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

from fastapi.testclient import TestClient

from server import app

PAGES = ("/", "/studio", "/services", "/cases", "/journal", "/demo", "/trust")
LIMIT_PER_ASSET = 700_000
LIMIT_TOTAL = 3_000_000


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        info = dict(attrs)
        if tag == "link" and info.get("rel") == "stylesheet":
            target = info.get("href", "")
        elif tag == "script" and "src" in info:
            target = info.get("src", "")
        else:
            return
        if target.startswith("/studio-assets/"):
            self.paths.add(target)


def collect() -> dict:
    client = TestClient(app)
    assets = defaultdict(set)
    failed = []
    for path in PAGES:
        response = client.get(path)
        if response.status_code != 200:
            failed.append(f"{path}: HTML status {response.status_code}")
            continue
        parser = AssetParser()
        parser.feed(response.text)
        for asset in parser.paths:
            assets[asset].add(path)

    measurements = []
    for path in sorted(assets):
        response = client.get(path)
        if response.status_code != 200:
            failed.append(f"{path}: static status {response.status_code}")
            continue
        length = len(response.content)
        if length > LIMIT_PER_ASSET:
            failed.append(f"{path}: {length} bytes exceeds per-file budget")
        measurements.append({
            "path": path,
            "bytes": length,
            "pages": sorted(assets[path]),
        })
    total = sum(item["bytes"] for item in measurements)
    if total > LIMIT_TOTAL:
        failed.append(
            f"{total} total referenced bytes exceeds asset inventory budget"
        )
    return {
        "page_count": len(PAGES),
        "asset_count": len(measurements),
        "unique_asset_bytes": total,
        "limits": {
            "per_asset": LIMIT_PER_ASSET,
            "unique_total": LIMIT_TOTAL,
        },
        "assets": measurements,
        "failures": failed,
        "note": (
            "Uncompressed static asset inventory, not transferred "
            "bytes, Lighthouse, CWV or production cache behavior."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        default=Path("artifacts/public-assets"),
    )
    args = parser.parse_args()
    result = collect()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# OMNIFACTORY public asset inventory",
        "",
        f"Pages: {result['page_count']}",
        f"Unique CSS/JS assets: {result['asset_count']}",
        f"Uncompressed bytes: {result['unique_asset_bytes']}",
        "",
        "| File | Bytes | Referencing pages |",
        "| --- | ---: | --- |",
    ]
    for item in result["assets"]:
        lines.append(
            "| " + item["path"] + " | "
            + str(item["bytes"]) + " | "
            + ", ".join(item["pages"]) + " |"
        )
    lines.extend(["", result["note"], "", "## Failures"])
    lines.extend(result["failures"] or ["None"])
    (args.output / "report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(
        "Public assets: "
        + str(result["asset_count"])
        + " files, "
        + str(result["unique_asset_bytes"])
        + " uncompressed bytes, "
        + str(len(result["failures"]))
        + " errors"
    )
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
