# Bot Lab Phase 4 — Railway BYOC resource binding and live status

## What changed

OMNIFACTORY Bot Lab now works with an **actual Railway service chosen by the
customer**, rather than showing only local plans. This feature deliberately
reads real infrastructure without creating, restarting or deleting it.

- Choose a **BYOC Railway deployment plan** in Bot Lab.
- Fetch projects using the customer's existing encrypted Railway OAuth token.
- Select project, service and environment from the authorized inventory.
- Verify ownership through Railway's `project(id)` GraphQL response before
  persisting the relationship in PostgreSQL.
- Inspect `serviceInstance(serviceId, environmentId)` for a real
  `latestDeployment.id/status`, region, number of replicas and whether a
  healthcheck path is configured.
- Store a customer-scoped `CloudRailwayBinding`; no tokens in this table.
- Unlink the binding safely without altering the Railway project.
- Add readiness blockers for unlinked resources and unverified application
  health. A Railway deployment status is **not** proof a Telegram bot is
  receiving updates or passes application-level health checks.

## HTTP API

`POST /api/v1/cloud/resources/bindings`: account login + CSRF; verified
`plan_id`, `project_id`, `service_id`, `environment_id`.

`GET /api/v1/cloud/resources/bindings/{plan_id}`: owned mapping.

`GET /api/v1/cloud/resources/bindings/{plan_id}/inspect`: fresh read of
provider deployment status. Updates the stored last-checked timestamp.

`DELETE /api/v1/cloud/resources/bindings/{plan_id}`: authenticated + CSRF;
remove mapping **only**, never delete provider resources.

Service identifiers are sent to Railway only after access checks. OAuth token
is decrypted server-side, not returned to the browser.

## Accepted only for BYOC

OMNIFACTORY Managed Cloud is a distinct operator-owned billing and isolation
mode. It does not assume a customer's Railway OAuth grant; accordingly this
feature only links BYOC plans. Managed Cloud release control requires a
separately configured operator provider account and tenant quotas.

## Security and reliability

- Project membership verified on every binding creation and status refresh.
- A customer cannot read a plan or binding owned by another account.
- The browser receives sanitized project/service/deployment fields only.
- Fixed GraphQL documents, short network timeout, no inherited proxy or
  redirects, streamed response capped at 128 KiB.
- No write operations on Railway in this PR.
- Customer OAuth expiration or revocation results in an error requiring
  refresh/reconnect, never an unauthorized fallback.
- A plan version is not a built image. Do not claim publication without
  verified OCI image, deployed service, startup probe and Telegram end-to-end
  test.
- Healthcheck *configuration* is reported, but no HTTP healthcheck is
  executed in this release.

## Testing on Windows / PyCharm

First, verify that your configured database is a test or development DB.
This branch includes a **new migration** `20261114_portal_08` based on 07;
it must not be applied to an unknown production/Neon DB.

```powershell
git fetch origin
git switch -c feat/bot-lab-release-ops-20261114 --track origin/feat/bot-lab-release-ops-20261114
.\.venv-clean\Scripts\python.exe -m pytest tests/test_railway_resource_bindings.py tests/test_bot_lab.py tests/test_railway_inventory.py -q --tb=short
```

Only after tests, schema review, target DB confirmation and backup:

```powershell
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini current
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini upgrade head
```

Start on an unoccupied port and open `/bots/lab`. Select a BYOC plan,
click `Загрузить ресурсы`, choose project, service and environment, then
`Привязать сервис` and `Проверить статус`.

## Next phase: actual managed release

These are **not** implemented in Phase 4:

1. Versioned, signed OCI runtime image from CI with verified SHA-256 digest.
2. Telegram BotFather credential vault with tenant access control.
3. Provider spending estimate, quota and explicit billing authorization.
4. Durable live provision worker that stores IDs after every mutation,
   distinguishes unknown outcomes and reconciles safely without duplicate
   creates.
5. Domain and Telegram webhook configuration with health-verified traffic
   cutover.
6. Logs, billing metering, restart and rollback with audited permissions.
7. Owner-operated Managed Cloud deployment for mass-market customers.

## API source

- https://docs.railway.com/integrations/api/manage-projects
- https://docs.railway.com/integrations/api/manage-services
- https://docs.railway.com/integrations/api/manage-deployments
