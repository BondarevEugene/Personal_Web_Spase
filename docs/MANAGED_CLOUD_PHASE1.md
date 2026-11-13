# OmniFactory Managed Cloud — Phase 1: planning foundation

## Product modes

**Managed Cloud**: OMNIFACTORY owns the hosting account and operates isolated
customer services. Customer only manages their bot, permissions, and costs
through OMNIFACTORY. The commercial product requires tenant quotas, metering,
billing, abuse controls, isolation, support and reliable incident response.

**Bring Your Own Cloud (BYOC)**: customer authorizes their Railway resources
through OAuth. OMNIFACTORY never asks for their Railway username/password and
must request only the OAuth scopes needed to provision and inspect services.

The provider interface intentionally separates cloud identity, deploy
planning and provisioning. Managed Cloud v1 targets Railway; additional
providers can be added without rewriting Graph Studio.

## This PR actually implements

- Pure validated Pydantic `DeploymentSpec` and deterministic plan hash.
- Mandatory monthly **budget CAP**, explicitly **not** a cost estimate.
- Safe `/api/v1/cloud/preview`, no tokens, no resource creation.
- Tenant-scoped, CSRF-protected, idempotent `/api/v1/cloud/plans` CRUD-read
  endpoints storing no credentials.
- Model and Alembic revision `20261114_portal_05` chained onto Portal
  Automation revision `20261114_portal_04`.
- `/cloud/deploy` form with managed/BYOC selection, transport and budget
  preferences; direct homepage navigation.
- Provider interfaces return truthful readiness statuses, and provisioning
  explicitly raises `NotImplementedError` until enabled in later phases.

## Next implementation stages — not yet available

### Phase 2: Railway OAuth and secret vault

- Create an OAuth application in Railway Developer settings.
- Authorization code + PKCE + state + exact redirect URI.
- Scope choices per workspace/project; `offline_access` only when justified.
- Encrypt refresh tokens at rest, separate operator-managed key, redact logs,
  support disconnect/revoke and token rotation.
- Vault for Telegram BotFather token and API credentials: never embed raw
  secrets in a user JSON graph or deployment ZIP.

### Phase 3: Provisioning and rollout

- Railway provider API implementation: project / environment / service /
  variables / immutable image, supported by official GraphQL API.
- Explicit approval for any billable resources. Estimate provider spend first.
- Durable queue with idempotent attempt records and operator permissions.
- Deploy stable pinned images, readiness healthcheck, gradual rollout,
  rollback on failure and audit logs.
- Telegram webhook/worker mode exclusivity; HTTPS endpoint and secret
  verification; single polling worker when required.

### Phase 4: Managed multi-tenant control plane

- Separate control plane from execution/data plane.
- Customer/organization quotas and accounting per running service.
- Isolation policy for independent user code, sandboxing, abuse detection.
- Usage and AI-cost metering; billing notices and spend alerts.
- Recovery, backups, logs, audit trail, SLOs and operator incident queue.

### Phase 5: Advanced automation & ecosystem

- Cloud Run and other providers, BYOC migration/export.
- Google/Meta OAuth consent, workflow agent modules, CRM linkage,
  domain/email/webhook routing, deployment doctor.
- Versioned bundles for GitHub/independent self-hosting.

## Safety and deployment policy

No `/cloud/deploy` action currently calls Railway. The plan has
`creates_resources=false` and `estimated_usd=null`. An entered budget cap
does NOT guarantee budget enforcement by Railway or OMNIFACTORY.
Do not imply a bot is live based on a planned state.

Never collect passwords for Railway, Telegram or Google.
For Telegram, creation of a bot in BotFather is a user action; accept its
token through a dedicated secure secret submission flow only when vault and
RBAC have been implemented.

Use official docs:
- https://docs.railway.com/integrations/oauth
- https://docs.railway.com/integrations/oauth/scopes-and-user-consent
- https://docs.railway.com/integrations/api
- https://docs.railway.com/integrations/api/manage-projects
- https://docs.railway.com/integrations/api/manage-services

## Local verification

Use a **development database**, not production Neon, before upgrading:

```powershell
git fetch origin
git switch -c feat/managed-cloud-foundation-20261114 --track origin/feat/managed-cloud-foundation-20261114
.\.venv-clean\Scripts\python.exe -m pytest tests/test_cloud_deploy.py -q
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini current
# Only after confirming the target DB is local/dev:
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini upgrade head
```

Then run `run.py` on an unoccupied local port and open `/cloud/deploy`.
Before merging, test all existing PR #25–27 migrations and regressions too.
