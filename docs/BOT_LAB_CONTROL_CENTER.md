# OMNIFACTORY Bot Lab — unified control room

## What it replaces

A previously public `/admin` dashboard was based on an obsolete template
with fabricated CPU/RAM, 99.8% uptime and invented execution counters.
It is **not** an operational truth source and must not be exposed as an
administrator panel.

`/bots/lab` (also `/bot-lab`) is the new authenticated workspace. All
legacy `/admin` routes redirect to the corresponding protected/public
canonical area. It does not grant administrative privileges or leak other
customers' data.

## Current delivered features — pending acceptance

- Dedicated high-contrast, responsive Bot Lab interface.
- Logged-in account's persisted Telegram Builder drafts from
  `portal_builder_projects`.
- Account's Automation Studio workflows and revisions from
  `portal_automation_workflows`.
- Account's Cloud Deploy plans from `portal_cloud_deployments`, correctly
  labelled `planned`, **not running**.
- Railway OAuth connection status and expiration from
  `portal_cloud_oauth_connections`.
- An explicitly user-initiated **read-only** Railway GraphQL project inventory,
  showing project names, service count and environment count, fetched
  from an authorized OAuth connection.
- Search and selection in one dashboard; actions open the existing
  working editors and Cloud Deploy planner.
- No fake logs, cost, deployment health or monitoring values.
- API test coverage for account login, multi-tenant isolation, schema parsing
  and GraphQL errors, including HTTP 200 with an `errors` array.
- New GitHub Actions smoke tests.

## Access and security

`GET /api/v1/bot-lab/overview` requires existing portal session and returns
only that customer's projects. No API secrets or Railway tokens are included.

`GET /api/v1/bot-lab/railway/projects` requires the same session, an unexpired
Railway OAuth grant and a valid Fernet vault key. The provider call is
read-only, uses a fixed GraphQL query, HTTPS, short timeout, no proxy
inherited from environment, no redirects, capped response size.

It does not mutate any external resource or create a billable Railway project.
Do not call a project `online` unless verified separately through
Railway deployment status **and** application healthcheck.

A failure to read projects is not automatically a failure of a deployed bot.
It may indicate expired OAuth, changed permissions or upstream outage.

## Next step: provisioning and lifecycle

To make "Publish" genuinely functional without accidental customer charges:

1. Confirm valid Railway OAuth scopes and selected workspace/project.
2. Freeze an immutable runtime version and configuration and build a
   reproducible deploy package.
3. Implement a durable provisioning job in PostgreSQL with explicit
   financial approval, idempotency, provider resource IDs and per-tenant limits.
4. Wire projectCreate/serviceCreate, deploy and domain settings with
   confirmed Railway GraphQL schema and a reconciliation worker.
5. Use a secret-vault based Telegram token reference, not user-provided
   passwords or tokens in project JSON.
6. Validate healthchecks, webhook exclusivity, live Telegram delivery,
   deploy statuses and rollback.
7. Add logs, costs, budget alerts, controlled restart and rollback actions.
8. Support Managed Cloud billing/quotas distinct from customer-owned BYOC.

## Local acceptance

After checking out this PR branch and verifying it points to a **development**
database containing migrations 01 through 06:

```powershell
.\.venv-clean\Scripts\python.exe -m pytest tests/test_bot_lab.py tests/test_railway_inventory.py -q --tb=short
.\.venv-clean\Scripts\python.exe run.py --port 8002
```

Then visit `http://127.0.0.1:8002/bots/lab`, login, check your saved drafts,
open a bot in Graph Studio, return to Lab, and inspect Railway projects if
your OAuth application and permissions are configured.

## Official Railway API documentation

- https://docs.railway.com/integrations/api
- https://docs.railway.com/integrations/api/manage-projects
- https://docs.railway.com/integrations/api/manage-services
- https://docs.railway.com/integrations/oauth
