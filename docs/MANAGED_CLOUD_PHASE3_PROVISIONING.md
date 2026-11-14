# OmniFactory Managed Cloud — Phase 3: Provisioning Job Foundation

## What is implemented

This stage turns Cloud Deploy plans into **durable, customer-owned job
requests** and runs a separate provisioning-simulation worker. It is the first
step toward reliable automated deployments, not a production release system.

- Account-scoped queue with mandatory session and CSRF token.
- Immutable manifest hash and frozen JSON per job; jobs never silently inherit
  later user edits.
- Unique per-customer idempotency key and status machine:
  `queued → running → simulated`, or `queued → cancelled`, or `running → failed`.
- Append-only event log (no credentials or request bodies).
- Separate explicit worker using atomic SQL compare-and-swap to avoid two
  worker processes claiming the same job.
- GraphQL Railway adapter for `projectCreate`, `serviceCreate`, and
  `serviceInstanceDeployV2` with fixed, typed mutations. The adapter is
  **not reachable by the worker or public API** until a verified live
  provisioning path has passed acceptance.
- New API:
  - `GET /api/v1/cloud/provision/capabilities`
  - `GET /api/v1/cloud/provision/jobs`
  - `POST /api/v1/cloud/provision/jobs`
  - `GET /api/v1/cloud/provision/jobs/{id}`
  - `POST /api/v1/cloud/provision/jobs/{id}/cancel`
- Bot Lab includes the simulation queue, status and event history.
- Database revision `20261114_portal_07` depends on revision `06`.
- Targeted tests and GitHub Actions workflow.

## Why real Railway mutation is deliberately disabled

Railway's GraphQL API supports actual project/service creation and deployment,
but write operations are **not guaranteed exactly-once**, and a transient
network failure can leave an unknown outcome. Creating another project after
a timeout might duplicate services and costs.

A simple budget input does not establish the current cost of running the
service or enforce a Railway spending cap.

Until the control plane has these controls, automated paid provisioning must
remain disabled:
1. Verifiable provider authorization for a **specific workspace/project**.
2. Quote or explicit accepted spend policy; enforced customer tenant quotas.
3. Immutable runtime image digest from our CI release pipeline.
4. Encrypted Telegram and API secret vault with user permissions.
5. Reconciliation after unknown provider outcome (query by IDs and carefully
   tagged ownership), no blind retry of external create mutations.
6. Persist provider resource IDs after each confirmed mutation.
7. Deployment readiness probe, logs, traffic activation and rollback.
8. Operational runbook, failure alerts and provider-specific e2e tests.

The Railway adapter is an integration boundary for a future vetted worker,
not a claim that the public product can currently deploy bots.

## Workflows: how the current simulation is executed

1. Log in to OmniFactory and visit `/bots/lab`.
2. Create a plan from `/cloud/deploy`.
3. Select the plan in the Lab sidebar.
4. Review readiness blockers.
5. Click **Добавить проверку в очередь** and explicitly confirm a
   simulation. No Railway resources are created.
6. On a **verified development database**, invoke the worker manually:
   ```powershell
   .\.venv-clean\Scripts\python.exe -m automation.provision_worker --once
   ```
7. Return to Bot Lab, click **Обновить задачи** and inspect event history.

No worker is started automatically from FastAPI. A production worker would
need a supervisor, operational visibility, security controls and a recovery
process.

## Migration/testing

After checking the DB target:

```powershell
git fetch origin
git switch -c feat/railway-provisioning-jobs-20261114 --track origin/feat/railway-provisioning-jobs-20261114
.\.venv-clean\Scripts\python.exe -m pytest tests/test_cloud_provisioning.py tests/test_bot_lab.py tests/test_cloud_deploy.py -q
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini current
# Run ONLY on confirmed local/dev DB, and only after tests pass:
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini upgrade head
```

## Provider documentation

- https://docs.railway.com/integrations/api/manage-projects
- https://docs.railway.com/integrations/api/manage-services
- https://docs.railway.com/integrations/api
