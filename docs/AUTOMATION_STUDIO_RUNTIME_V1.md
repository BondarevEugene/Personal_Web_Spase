# OMNIFACTORY Automation Studio — runtime v1

## Scope and identity

Automation Studio is a Python-first declarative workflow system, not a fork
or copy of n8n. It shares OmniFactory customer sessions with Graph Studio but
has an independent workflow graph, run ledger and execution API.

**One source of truth:** `automation/engine.py` validates and interprets
execution graphs. Frontend controls must not claim a provider works unless a
real connector action is supported.

## Implemented in this branch — pending local acceptance tests

- Visual editor `/automation/studio` with categorized movable nodes, ports,
  true/false edges, inspector, customer-owned workflow save/load and live trace
  of test runs.
- `trigger`, `set`, `transform` (upper/lower/strip), `condition`
  (equals/not-equals/contains/not-empty/greater/less), `end`.
- `approval` safely stops a run. **Resume is NOT implemented**. Approval is
  not falsely presented as a working approval inbox.
- Max 80 nodes/definition, 50 steps/execution, 64 KiB data and at most 3
  external requests. No eval, subprocess, exec, arbitrary user Python.
- `http` for operator-allowlisted HTTPS destinations, with live custom HTTP
  requiring both explicit opt-in and a trusted egress proxy.
- Operator-managed external credentials for: Google Docs `create`, Google
  Sheets `append`, Facebook Pages `publish`, Instagram `publish_image`.
  **These connector calls require real authorized provider tokens and external
  integration testing before a production-ready claim.** Interactive OAuth
  setup and refreshed access tokens are not implemented.
- Run audit: per-user workflow/revision, status, dry-run/live, limited trace,
  timestamp; no raw request bodies or secret values in trace.
- Idempotency key required for **live** calls; execution row is reserved
  before any effects. Concurrent duplicate keys cannot create a second run.
  A crashed live execution is left as `running` for manual reconciliation.
- Authenticated account CRUD; optimistic revision protection on workflow edits.
- Individually token-protected inbound Webhook; raw token is shown once, only
  SHA-256 stored. **Webhook execution is dry-run-only**.
- Recurring interval schedule (5–10080 minutes) with independent DB worker,
  atomic claim of due ticks and dry-run-only executions.
- Explainable static preflight audit with reachable nodes, risk warnings and
  recommendations. The audit is heuristic and **not a security certification**.

## Not implemented yet

- Secure customer-managed OAuth consent/refresh for Google and Meta;
  connector permission/scopes verification.
- Host/cluster deployment of exported Telegram bots.
- Arbitrary Python handler: requires isolation, quotas, sandbox security,
  package allowlist and lifecycle management. Never run user Python in
  FastAPI workers.
- Durable human-approval resume and manual review inbox.
- Long-running queue workers, dead-letter queue, per-connector retry policies.
- Cron expression schedules, distributed scale, workflow version rollback,
  operational metrics and AI cost ledger.
- Bidirectional integration with OmniFactory CRM and Food_Porn.
- Public production readiness, penetration testing, provider end-to-end tests.

## Database

Migrations form a chain:
`20261109_portal_01` → `20261109_portal_02` →
`20261113_portal_03` → `20261114_portal_04`.

**Before migration, verify the environment points to the intended DB.**
Local default is `portal_dev.sqlite3`. Neon migrations require
`OMNI_PORTAL_MIGRATION_URL` pointing to the **direct** endpoint, not pooler.
Do not run migrations against an unknown production database.

PowerShell from repository root:

```powershell
.\.venv-clean\Scripts\python.exe -m pytest tests/test_automation_engine.py tests/test_automation_api.py tests/test_automation_schedule.py tests/test_automation_studio.py -q
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini current
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini upgrade head
.\.venv-clean\Scripts\python.exe run.py --port 8002
```

Visit `http://127.0.0.1:8002/automation/studio` when this local port is free.
Refresh after backend changes and verify with `/docs`.

## API

`GET /api/v1/automation/catalog`: machine-readable supported nodes and
limitations.
`POST /api/v1/automation/analyze`: static preflight without side effects.
`GET/POST /api/v1/automation/workflows`: owned definitions.
`GET/PUT/DELETE /api/v1/automation/workflows/{id}`: get/update/delete.
`POST /api/v1/automation/workflows/{id}/runs`: execution, dry by default.
`GET /api/v1/automation/workflows/{id}/runs`: run history.
`GET/PUT/DELETE /api/v1/automation/workflows/{id}/schedule`: interval.
`POST/DELETE /api/v1/automation/workflows/{id}/webhook`: rotate/revoke.
`POST /hooks/automation/{id}`: token-protected inbound event; dry only.

Mutating authenticated calls require `X-Omni-CSRF` from the existing
customer portal CSRF endpoint. A live run additionally requires
`Idempotency-Key`, owner role, explicit `live=true`, and operator opt-in.

## Connector configuration: operator, not end-user

All connectors default to dry-run. Live mode is off until the operator sets:

- `OMNI_AUTOMATION_LIVE_ENABLED=1` — general live opt-in.
- `OMNI_CREDENTIAL_GOOGLE` — a valid Google OAuth access token with the
  appropriate Docs or Sheets scope; never put the token in a graph.
- `OMNI_CREDENTIAL_FACEBOOK` — a permitted Page access token.
- `OMNI_CREDENTIAL_INSTAGRAM` — a permitted professional IG token.
- `OMNI_AUTOMATION_ALLOWED_HOSTS` — exact hostnames for custom HTTP, comma
  separated; no wildcards.
- `OMNI_AUTOMATION_HTTP_LIVE_ENABLED=1` — **additional** opt-in for custom HTTP.
- `OMNI_AUTOMATION_EGRESS_PROXY` — operator-managed security egress proxy;
  production SSRF defenses require filtering/monitoring at this proxy and/or
  network policy. DNS inspection inside Python alone is insufficient.

Environment secrets must be injected by the hosting platform and must not
be written to `.env` files committed to Git. Do not blindly enable live
for a customer-editable graph.

## Recurring worker

The HTTP app does **not** start a scheduler on import or boot.
Start the dedicated worker explicitly when required:

```powershell
.\.venv-clean\Scripts\python.exe -m automation.scheduler --once
# Or as a separate supervised service:
.\.venv-clean\Scripts\python.exe -m automation.scheduler --loop
```

A schedule only fires while a worker is running, and it executes dry-runs.
Scheduling actual provider writes needs further operational controls and
provider-specific idempotency semantics.

## Competitive advantages (built or designed)

1. **Explainable traces:** which branch was taken and why.
2. **Safety-first:** dry-run by default, bounded execution and explicit live gates.
3. **Transparent project history:** owned graph revisions and run audit.
4. **Human control:** approval is a first-class stop point; resume work pending.
5. **Python-native extension path:** static graph interpreter now; isolated
   Python workers only after sandbox hardening.
6. **Audit before deployment:** deterministic review of broken paths, missing
   configuration and side-effect risks (not a formal security audit).

These are product differentiators, not claims of full n8n feature parity.

## Sources and API reference

- Google Docs API: https://developers.google.com/workspace/docs/api/concepts/request-response
- Google Sheets API: https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values/append
- Meta Page publishing: https://developers.facebook.com/docs/graph-api/reference/page/feed/
- Instagram publishing: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media

Review provider release notes, permissions and APIs before enabling live.
