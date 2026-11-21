"""Release readiness manifest from the repository, no network or secrets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITICAL = {
    "runtime": ("Dockerfile", "railway.json", "server.py"),
    "public": ("index.html", "omni_site/router.py", "omni_site/templates/solution_demo.html"),
    "customer": ("portal/routes.py", "portal/workspace_center.py"),
    "automation": ("api/automation.py", "api/automation_connections.py"),
    "builder": ("api/simple_builder.py", "api/builder_projects.py"),
    "migration": ("portal_alembic.ini", "portal/migrations/env.py"),
    "staging": ("scripts/verify_platform_staging.py", "docs/RAILWAY_PLATFORM_RELEASE.md"),
}


def inventory(root: Path = ROOT) -> dict:
    modules = {}
    for group, paths in CRITICAL.items():
        modules[group] = {
            "ready": all((root / path).is_file() for path in paths),
            "files": [{"path": path, "exists": (root / path).is_file()} for path in paths],
        }
    return {"ready": all(group["ready"] for group in modules.values()), "modules": modules}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable inventory")
    args = parser.parse_args(argv)
    report = inventory()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for group, details in report["modules"].items():
            print(f"{group}: {'OK' if details['ready'] else 'MISSING'}")
            for file in details["files"]:
                if not file["exists"]:
                    print(f"  missing: {file['path']}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
