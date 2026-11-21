# OMNIFACTORY Managed Cloud — Secure Release Gate (Phase 5)

## Purpose

Bot Lab now supports an immutable release review requested by the bot's
registered owner, to lay a safe foundation for future **one-click deployment**.
A review is **not** a Railway publish action and is **not** consent to
unlimited infrastructure spending.

## What is implemented

- Dedicated Release Control section under `/bots/lab` (OMNI style).
- An explicit bot + Cloud Deploy plan selection, checked server-side against
  the authenticated **owner**; invitations grant no release permissions.
- Explicit Telegram `getMe` verification status from the existing
  per-bot encrypted vault. Plaintext credentials never leave the vault.
- Operator-configured immutable image digest allowlist,
  `OMNI_RELEASE_IMAGE_TELEGRAM_AIOGRAM`. The image must be in canonical
  `registry/repository@sha256:<64 lowercase hex>` form.
- Existing Railway BYOC mapping and unexpired OAuth checked. Managed Cloud
  operator-owned billing path remains blocked until isolated infrastructure
  pools, quotas and secret distribution exist.
- A transparent server-side readiness checklist including **hard blockers**
  for missing provider pricing quote / enforced budget, unimplemented live
  worker and unverified webhook/application health.
- Authenticated + CSRF-protected, owner-only review creation, explicit
  `REQUEST RELEASE REVIEW` phrase, per-owner idempotency, 24h expiry,
  immutable snapshot of scenario hash, plan hash, token ciphertext
  fingerprint, pinned image digest, owner IDs and accepted **budget cap**.
- Change a bot scenario, rotate Telegram token, disconnect Railway, remove
  binding, or change operator's release image: old review immediately
  reports `still_valid=false` on read.
- Owner can cancel a review. Audit events record only safe IDs/action codes.
- No public worker route can resolve Telegram credentials or call Railway
  billable GraphQL mutations in this phase.

## Security contract

- No token plaintext, OAuth credential or webhook secret returned by
  `/api/v1/cloud/releases`.
- No user-controlled registry/image allowed in API: digest comes from
  `OMNI_RELEASE_IMAGE_TELEGRAM_AIOGRAM` on the server only.
- The digest being configured does **not** prove that the container exists,
  was vulnerability-scanned, signed, or is running. Supply an image produced
  by controlled CI release and verify signature/provenance in a future stage.
- `review_requested` is **never** `approved_for_deploy`,
  `deployed` or `online`. A worker must not interpret it as financial
  consent or a provider authorization.
- This phase does not upload containers, call Railway mutation APIs, set
  webhook or create or charge infrastructure.

## Production rollout prerequisites

1. Build and sign reviewed Docker images with immutable OCI SHA-256 digests,
   pin dependencies, scan SBOM/vulnerabilities and retain release provenance.
2. Configure a dedicated worker identity with least privilege and a
   customer/organization secret store with KMS-backed encryption.
3. Check the specific Railway workspace's service-level permissions,
   approved project, owner and available spending budget.
4. Obtain a real provider cost estimate or explicit customer agreement and
   prove that Railway compute usage limits are configured and appropriate.
   A workspace hard limit can stop *all* workloads; it is not a per-bot cap.
5. Implement mutating operations with persisted remote resource IDs,
   idempotent jobs, safe reconciliation of unknown outcomes, and rollback.
6. Verify container status AND application `/health`, Telegram webhook,
   endpoint secret, real message processing and tenant isolation before
   status `online`.
7. Add SLOs, alerting, request rate limits, audit retention, incident
   runbooks and operator approval before serving customer credentials.

## Environment

Use a secure server-side variable for an approved image:

```text
OMNI_RELEASE_IMAGE_TELEGRAM_AIOGRAM=registry.example/omni/telegram-runtime@sha256:<verified-64-character-hex-digest>
```

This is **illustrative only**. Do not paste the placeholder into production
or fabricate a digest. Until the operator configures a real approved digest,
the release preflight correctly blocks review.

## Routes

- `GET /api/v1/cloud/releases/capabilities`
- `GET /api/v1/cloud/releases/preflight/{bot_id}/{plan_id}`
- `POST /api/v1/cloud/releases/reviews`
- `GET /api/v1/cloud/releases/reviews`
- `GET /api/v1/cloud/releases/reviews/{id}`
- `POST /api/v1/cloud/releases/reviews/{id}/cancel`

## Local acceptance

```powershell
git fetch origin
git switch -c feat/managed-cloud-secure-release-20261114 --track origin/feat/managed-cloud-secure-release-20261114
.\.venv-clean\Scripts\python.exe -m pytest tests/test_secure_release.py tests/test_bot_security.py -q --tb=short
```

On a **verified development** DB, after a backup and schema review:
```powershell
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini current
.\.venv-clean\Scripts\python.exe -m alembic -c portal_alembic.ini upgrade head
```

The latest migration is `20261114_portal_10` based on 09.

Then open `/bots/lab`: select owned bot → select plan → check readiness.
A request can be saved only after the nonfinancial prerequisites pass; real
deployment will remain blocked until dedicated production gates exist.

## Railway cost controls

- https://docs.railway.com/pricing/cost-control
- https://docs.railway.com/pricing
- https://docs.railway.com/cli/usage
