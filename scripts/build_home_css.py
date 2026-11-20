"""Build the one-request homepage feature stylesheet, preserving layer order.

Source files remain authoritative and individually served on other pages.
Use --check in CI to fail on a stale committed bundle.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

STATIC = Path(__file__).resolve().parents[1] / "omni_site" / "static"
SOURCES = (
    "platform.css",
    "founders.css",
    "unified_shell.css",
    "public_growth.css",
    "demo_home.css",
    "case_home.css",
    "services_home.css",
    "trust_home.css",
    "visual_excellence.css",
)
OUTPUT = "home_features.bundle.css"


def build() -> str:
    pieces = [
        "/* GENERATED FILE — do not edit. Run "
        "python -m scripts.build_home_css instead. */\n",
    ]
    for name in SOURCES:
        payload = (STATIC / name).read_text(encoding="utf-8")
        if "@import" in payload:
            raise ValueError(
                f"{name} contains @import; bundle order must be reviewed"
            )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
        pieces.append(
            f"\n/* BEGIN {name} SHA256:{digest} */\n"
            + payload.rstrip()
            + f"\n/* END {name} */\n"
        )
    return "".join(pieces)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="Fail if the checked-in generated CSS differs from sources",
    )
    args = parser.parse_args()
    expected = build()
    destination = STATIC / OUTPUT
    if args.check:
        if not destination.exists():
            print("Missing generated CSS bundle:", destination)
            return 1
        if destination.read_text(encoding="utf-8") != expected:
            print(
                "Stale homepage CSS bundle. "
                "Run python -m scripts.build_home_css"
            )
            return 1
        print("Homepage feature bundle is current.")
        return 0
    destination.write_text(expected, encoding="utf-8")
    print(
        f"Built {destination.name}: {len(expected.encode('utf-8'))} "
        f"bytes from {len(SOURCES)} ordered sources"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
