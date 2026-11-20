"""Read-only, secret-safe production readiness assessment for OMNIFACTORY.

Run: python -m portal.release_doctor --json --production
Exit 0 only if all blocking checks pass. No migrations, writes, or network calls
other than a bounded SQL SELECT when --database is requested.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from portal.db import database_url

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_ASSETS = (
    "portal/templates/dashboard.html",
    "portal/templates/account_security.html",
    "portal/templates/client_projects.html",
    "portal/templates/client_project_detail.html",
    "portal/templates/client_finance.html",
    "portal/templates/client_notifications.html",
    "portal/templates/client_project_operator.html",
    "portal/templates/_workspace_nav.html",
    "omni_site/static/client_workspace.css",
    "omni_site/static/graph_studio.js",
    "omni_site/static/graph_groups.js",
)
EXPECTED_TABLES = (
    "portal_customers",
    "portal_organizations",
    "portal_sessions",
    "portal_settings",
    "portal_client_projects",
    "portal_client_project_milestones",
    "portal_client_project_events",
    "portal_client_project_documents",
    "portal_client_project_approvals",
    "portal_client_project_notifications",
    "portal_client_project_attachments",
    "portal_registration_events",
    "portal_plans",
    "portal_subscriptions",
    "portal_invoices",
    "portal_payments",
    "portal_gateway_events",
    "portal_builder_projects",
    "portal_automation_workflows",
    "portal_automation_runs",
    "portal_support_tickets",
    "portal_support_messages",
    "portal_support_events",
)


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    explanation: str


def check(name: str, ok: bool, explanation: str) -> Check:
    return Check(name, "pass" if ok else "fail", explanation)


def assess_config(*, production: bool, env: dict[str, str] | None = None,
                  root: Path = ROOT) -> list[Check]:
    """Pure config/files checks. Do not display values of credentials."""
    config = dict(os.environ if env is None else env)
    result: list[Check] = []
    db_url = config.get("OMNI_PORTAL_DATABASE_URL", "")
    migration = config.get("OMNI_PORTAL_MIGRATION_URL", "")
    csrf = config.get("OMNI_PORTAL_CSRF_SECRET", "")
    if production:
        result.append(check(
            "portal_database", db_url.startswith(("postgresql://", "postgresql+")),
            "Production must use an explicit PostgreSQL URL (not SQLite).",
        ))
        result.append(check(
            "direct_migration_url", migration.startswith(("postgresql://", "postgresql+"))
            and "-pooler." not in migration.lower(),
            "Set OMNI_PORTAL_MIGRATION_URL to a DIRECT Neon PostgreSQL endpoint.",
        ))
        result.append(check(
            "csrf_secret", len(csrf.encode("utf-8")) >= 32,
            "Set the SAME stable OMNI_PORTAL_CSRF_SECRET (>=32 bytes) on all workers.",
        ))
        result.append(check(
            "registration_policy",
            config.get("OMNI_PORTAL_ALLOW_REGISTRATION", "") in {"0", "1"},
            "Explicitly configure self-service registration (0 or 1).",
        ))
        result.append(check(
            "https_external_url",
            config.get("OMNI_PUBLIC_BASE_URL", "").startswith("https://"),
            "Configure OMNI_PUBLIC_BASE_URL with the public HTTPS origin.",
        ))
    else:
        result.append(Check("environment", "pass", "Local-development checks enabled."))
    origins = [v.strip() for v in config.get("OMNIFACTORY_CORS_ORIGINS", "").split(",")
               if v.strip()]
    result.append(check(
        "cors_policy", "*" not in origins and all(
            (parsed.scheme == "https" if production else parsed.scheme in {"http", "https"})
            and bool(parsed.netloc) and not parsed.username and not parsed.password
            for value in origins for parsed in (urlsplit(value),)
        ),
        "Only explicit trusted CORS origins; never wildcard or embedded credentials.",
    ))
    result.append(check(
        "migration_not_pooler",
        "-pooler." not in migration.lower(),
        "Schema migrations must never use a transaction pooler.",
    ))
    missing = [item for item in REQUIRED_ASSETS if not (root / item).is_file()]
    result.append(check(
        "workspace_assets", not missing,
        "Required client and Graph Studio assets are present." if not missing
        else "Missing: " + ", ".join(missing),
    ))
    return result


def assess_routes() -> list[Check]:
    """Check the published contract for the main customer and studio flows."""
    from server import app

    routes = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    required = {
        ("/health", "GET"),
        ("/account", "GET"),
        ("/account/login", "GET"),
        ("/account/register", "GET"),
        ("/account/security", "GET"),
        ("/account/security/password", "POST"),
        ("/account/projects", "GET"),
        ("/account/projects/{id}", "GET"),
        ("/account/projects/{id}/accept", "POST"),
        ("/account/projects/{id}/request-changes", "POST"),
        ("/account/projects/{id}/attachments", "POST"),
        ("/account/notifications", "GET"),
        ("/account/finance", "GET"),
        ("/account/finance/export.csv", "GET"),
        ("/support/projects", "GET"),
        ("/support/projects/{id}/status", "POST"),
        ("/architect", "GET"),
        ("/api/v1/builder/simple/export", "POST"),
    }
    missing = sorted(required - routes)
    return [check(
        "public_route_contract", not missing,
        "Client, operator, and Graph Studio routes are registered."
        if not missing else
        "Missing routes: " + ", ".join(f"{method} {path}" for path, method in missing),
    )]


def assess_database() -> list[Check]:
    """Read-only DB version/structure probe with no SQL or URL leaks."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from sqlalchemy import inspect

    output: list[Check] = []
    script = ScriptDirectory.from_config(Config(str(ROOT / "portal_alembic.ini")))
    heads = set(script.get_heads())
    output.append(check(
        "migration_graph", len(heads) == 1,
        "Alembic contains exactly one schema head." if len(heads) == 1
        else "Resolve divergent Alembic heads before deployment.",
    ))
    engine = None
    try:
        # Create a separate short-lived engine; never mutate production DB.
        url = make_url(database_url())
        engine = create_engine(
            url,
            connect_args={"connect_timeout": 5}
            if url.get_backend_name() == "postgresql" else {},
            pool_pre_ping=True,
        )
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            tables = set(inspect(connection).get_table_names())
            missing = sorted(set(EXPECTED_TABLES) - tables)
            output.append(check(
                "required_tables", not missing,
                "All required portal tables are present." if not missing
                else "Missing portal tables: " + ", ".join(missing),
            ))
            if "alembic_version" in tables:
                versions = {
                    row[0] for row in connection.execute(
                        text("SELECT version_num FROM alembic_version")
                    )
                }
                output.append(check(
                    "migration_head", versions == heads,
                    "Applied schema matches the single Alembic head." if versions == heads
                    else "Database migration is not at the current Alembic head.",
                ))
            else:
                output.append(check(
                    "migration_head", False, "Database lacks alembic_version.",
                ))
    except Exception:
        # Drivers and connection exceptions may contain user/password/host.
        output.append(check(
            "database_connection", False,
            "Database probe failed. Check credentials, network and direct URL privately.",
        ))
    else:
        output.append(check("database_connection", True, "Read-only SELECT 1 succeeded."))
    finally:
        if engine is not None:
            engine.dispose()
    return output


def assess(*, production: bool = False, database: bool = False,
           routes: bool = False, env: dict[str, str] | None = None, root: Path = ROOT) -> dict:
    checks = assess_config(production=production, env=env, root=root)
    if database:
        # DB probe only when explicitly requested; prevents accidental access.
        checks.extend(assess_database())
    if routes:
        checks.extend(assess_routes())
    if production and not database:
        checks.append(check(
            "database_probe_requested", False,
            "Production gate requires --database (read-only SQL checks).",
        ))
    if production and not routes:
        checks.append(check(
            "route_probe_requested", False,
            "Production gate requires --routes (FastAPI contract checks).",
        ))
    failed = sum(item.status == "fail" for item in checks)
    return {
        "service": "omni-client-workspace",
        "mode": "production" if production else "development",
        "ready": failed == 0,
        "passed": len(checks) - failed,
        "failed": failed,
        "checks": [asdict(item) for item in checks],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--database", action="store_true",
                        help="Explicitly perform a read-only database probe.")
    parser.add_argument("--routes", action="store_true",
                        help="Check FastAPI route registration (imports the app).")
    parser.add_argument("--json", action="store_true", help="Machine-readable output.")
    args = parser.parse_args()
    report = assess(production=args.production, database=args.database,
                    routes=args.routes)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["checks"]:
            print(f"{item['status'].upper():4} {item['name']}: {item['explanation']}")
        print("READY" if report["ready"] else "NOT READY")
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
