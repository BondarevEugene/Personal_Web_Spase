"""Build the one-request homepage CSS from the current two authoritative layers.

Preserves the site.css @import as the first rule and the homepage feature order.
The existing build_home_css.py remains authoritative for the feature layer.
"""
from __future__ import annotations

import argparse
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "omni_site" / "static"
OUTPUT = STATIC / "home_page.bundle.css"
SOURCES = ("site.css", "home_features.bundle.css")
HEADER = "/* GENERATED FILE — run python -m scripts.build_home_page_css */\n"


def build() -> str:
    pieces = [HEADER]
    for name in SOURCES:
        content = (STATIC / name).read_text(encoding="utf-8").rstrip()
        pieces.append(f"/* BEGIN {name} */\n{content}\n/* END {name} */\n")
    return "".join(pieces)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = build()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            print("Homepage CSS bundle stale: python -m scripts.build_home_page_css")
            return 1
        print("Homepage CSS bundle current")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"Built {OUTPUT.name}: {len(expected.encode('utf-8'))} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
