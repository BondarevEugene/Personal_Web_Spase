# OMNIFACTORY — Production Release Gate

Read-only pre-deployment diagnostics for Client Workspace and Graph Studio.

## Usage (Python 3.12 / PowerShell)

Run from repository root after installing requirements:

    python -m portal.release_doctor --production --routes --database --json
    python -m ruff check .
    python -m pytest -q tests/test_platform_release_doctor.py
    python -m pytest -q

To validate local project assets and registered routes without connecting to Neon:

    python -m portal.release_doctor --routes --json

Exit status: 0 means all checked gates passed; 2 means a blocking check failed.
The report does NOT include credentials, tokens, CSRF secret, or database URLs.

## Production environment configuration

- OMNI_PORTAL_DATABASE_URL: explicit PostgreSQL URL, not local SQLite.
- OMNI_PORTAL_MIGRATION_URL: DIRECT Neon PostgreSQL URL (not pooler).
- OMNI_PORTAL_CSRF_SECRET: stable secret, at least 32 bytes, equal across workers.
- OMNI_PORTAL_ALLOW_REGISTRATION: explicitly 0 or 1.
- OMNI_PUBLIC_BASE_URL: HTTPS origin to declare intended public endpoint.
- OMNIFACTORY_CORS_ORIGINS: blank for same origin or trusted HTTPS origins only.

OMNI_PUBLIC_BASE_URL is an asserted configuration value used by this doctor;
it does not configure a reverse proxy or prove public HTTPS is reachable.
Check TLS, proxy host/scheme forwarding and session cookies on the real host.

## Database and Alembic

The opt-in --database check runs SELECT 1 and verifies that required portal
tables are present and alembic_version matches the single repository head.
It never creates tables, upgrades schema or writes application data.

If schema is outdated, run a separate controlled migration using DIRECT Neon:

    python -m alembic -c portal_alembic.ini upgrade head

Ensure there is a verified database backup before running production migrations.
Re-run the release doctor after migration.

## Manual business acceptance (GO / NO-GO)

1. Client and independent organization: all account, project, finance and
   notification pages must be tenant-isolated.
2. Customer and authorized operator: request project, plan stages, publish
   technical specification, approve latest revision, implement and submit
   delivery, request changes, resubmit and accept.
3. Upload/download project PDF or picture; old file versions preserved and
   another organization receives 404. Enforce multipart ingress limits.
4. In Graph Studio: create a branching scenario, simulate, debug, export ZIP,
   and execute generated aiogram bot using a separate test Telegram token.
5. Change UA/RU/EN, sign in from two browsers, rotate password; old session
   must be revoked immediately.
6. Run full pytest, Ruff, mobile browser checks and real public HTTPS checks.
7. Verify that logs and CSV/HTML responses do not contain credentials.

Do NOT consider the platform production-ready solely because /health returns OK
or because the static release doctor is green. Confirm with real browser,
Neon and deployed host tests.

This PR does NOT implement payment acquisition, auto-deployed bot hosting, MFA,
automatic production backups, outbound delivery alerts or malware scanning.
