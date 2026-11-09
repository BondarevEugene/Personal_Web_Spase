# OmniFactory Customer Portal — Neon foundation (Phase 2)

This is an **account, organization and billing-data foundation**. It is not yet a fully launched, publicly secure multi-tenant SaaS.

## Implemented
- /account/register — email, unique login, name, organization, Argon2id password
- /account/login — login **or** email + password, process-local throttling
- /account — private organization dashboard and real recorded accounting data (no fabricated revenue)
- /account/settings — language (ru/uk/en), timezone, marketing opt-in and name
- /account/logout — server-side revocation of a random session token
- Tables: portal_organizations, portal_customers, portal_sessions, portal_settings,
  portal_registration_events, portal_subscriptions, portal_invoices, portal_payments.
- Every registration creates an event and a free (0 UAH) subscription.
- Payments and invoices are isolated by org_id in the current read-side portal. No endpoint allows self-crediting.
- Login uses an HttpOnly SameSite cookie with a random opaque token; the DB stores only its SHA256 digest.
- POST forms require a CSRF cookie and form token.
- Browser views use Studio v3 typography and colors.

## Local setup on Windows
Before startup, install the additional dependencies and apply the isolated portal migration:

    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m alembic -c portal_alembic.ini upgrade head
    .\.venv\Scripts\python.exe run.py

By default portal tables are installed into **portal_dev.sqlite3** in the project root, separate from the pre-existing omnifactory.db. This is for local testing only; it is gitignored.

## Connect Neon (no credentials in Git or chat)
1. Create a dedicated Neon project/database and least-privilege database role for customer portal.
2. Neon Console → **Connect**. Obtain a pooled connection URL for the running web app and a **direct** URL for migrations. Both should use TLS and retain the connection parameters supplied by Neon.
3. Set the two environment variables in your IDE or hosting secret manager, **not** in Git:

    OMNI_PORTAL_DATABASE_URL=postgresql://...-pooler.../dbname?sslmode=require
    OMNI_PORTAL_MIGRATION_URL=postgresql://.../dbname?sslmode=require

4. Run migrations with the direct endpoint:

    .\.venv\Scripts\python.exe -m alembic -c portal_alembic.ini upgrade head

5. Run the server and visit http://127.0.0.1:8000/account/register.

Do **not** share the URL, DB username, password, API token or secrets in chat. Never expose the Neon URL to client-side JavaScript.

## Commercial policy
Registration is **not** an automatic purchase. A record is made with source and timestamp; the free plan is 0 UAH. Paid plan amounts, real invoices, payment gateway integrations, verified provider webhooks, refunds, recurring billing and tax/fiscal documents require product decisions and separate payment-provider development.

## Production blockers (must resolve before taking real customers)
- Email verification, recovery/reset flow, MFA for sensitive operations, distributed login throttling, session cleanup and audit logging.
- CSRF uses a signed double-submit cookie. For multi-worker production set a stable random OMNI_PORTAL_CSRF_SECRET on all app instances; stronger session-bound tokens and additional origin checks can be added in hardening.
- Reconcile shared privileges across legacy /admin and separate OmniBotCRM; do not grant customer login access to legacy admin.
- Builder graph projects are still saved client-side; real project ownership and tenant-isolated persistence must be added.
- Introduce secure user-account activation/paid entitlement enforcement before enabling paid functionality.
- Ensure secure TLS proxy setup. Remote HTTP account requests are rejected.
- Firebase Admin SDK key previously committed to Git must be revoked, and Git history remediated separately.

## Smoke tests
    .\.venv\Scripts\python.exe -m pytest -q tests/test_customer_portal.py

Tests run migrations against an isolated temporary SQLite DB and do not connect to Neon.

## Read-only commercial accounting report
After migrations, run from the repository root:
    .\.venv\Scripts\python.exe -m portal.report

It lists registration totals, signups by month, plan breakdown, invoice statuses
and confirmed revenue, without revealing personal user data.
Payment gateway is not yet connected; signup is not treated as paid revenue.

## Version verification when / still shows EVO MASTER
The new root sends HTTP header X-Omni-UI: studio-v3-platform.
GET /health contains platform_ui=studio-v3-platform and
customer_portal=accounts-v1 on this branch.
Check the branch and server process before troubleshooting CSS.

Revenue is reported per currency in confirmed_revenue_by_currency_minor; amounts from different currencies are never added together.
