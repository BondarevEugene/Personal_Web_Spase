# OMNIFACTORY Managed Cloud — Telegram Runtime v1

## Delivered in this phase

This PR introduces a real **standalone** containerized aiogram/ FastAPI
Telegram webhook runtime. It is deliberately separate from OmniFactory's
multi-tenant control plane and portal. The runtime can execute validated
Graph Studio scenario nodes: message, choice, input, condition, set_variable,
photo, document and end.

- Production-style Python 3.12 Dockerfile with a **non-root** UID.
- Pinned dependencies in `runtime/telegram/requirements.txt`.
- Bounded `OMNI_SCENARIO_BASE64` scenario passed through a deployment
  configuration interface; no BotFather credential is embedded in the image.
- `BOT_TOKEN` and `TELEGRAM_WEBHOOK_SECRET` are separate environment
  secrets and must be injected by a future isolated worker.
- `POST /telegram/webhook` checks Telegram's
  `X-Telegram-Bot-Api-Secret-Token` with constant-time comparison.
- Request payloads capped at 1 MiB; malformed updates are rejected.
- `GET /health` reports only **process_ready**; it does NOT falsely report
  Telegram delivery as operational.
- Read-only, owner-scoped `GET /api/v1/cloud/runtime/preflight/{bot_id}`
  validates the saved bot graph without exposing secrets or scenario text
  to unowned accounts.
- Runtime Inspector in `/bots/lab`: compatibility, configured image digest,
  current security limitations and missing production requirements.
- No Railway API write actions or customer charges.

## Build locally

```powershell
docker build -f runtime/telegram/Dockerfile -t omnifactory-telegram-runtime:test .
```

**Do not run this container with real customer tokens yet.** It needs
stronger state isolation and a deployment gate first.

For syntax and non-billable integration tests:

```powershell
.\.venv-clean\Scripts\python.exe -m pip install aiogram==3.22.0
.\.venv-clean\Scripts\python.exe -m pytest tests/test_telegram_runtime_v1.py tests/test_secure_release.py -q --tb=short
```

## Required deployment configuration

| Name | Classification | Purpose |
| --- | --- | --- |
| BOT_TOKEN | Secret | BotFather Telegram token, from dedicated Bot Vault |
| TELEGRAM_WEBHOOK_SECRET | Secret | Random 32–128 characters, used for Telegram header |
| OMNI_SCENARIO_BASE64 | Config | Bounded base64-encoded scenario, must be generated from validated project revision |
| PORT | Config | Port injected by Railway, default 8000 |

Use HTTPS and restrict the public endpoint to the intended Telegram webhook
path. The trusted release worker must set `setWebhook` only after a
successful deployment and healthcheck, and verify `getWebhookInfo` after
the change; `getUpdates` cannot operate simultaneously with a webhook.

Official Telegram documentation:
- https://core.telegram.org/bots/api
- https://core.telegram.org/bots/webhooks

## Critical limitations (do NOT claim production readiness)

- All dialogue cursors and values are **in memory**.
- A restart resets chats; multiple container replicas are not coordinated.
- No persistent `update_id` receipts/deduplication; Telegram might retry.
- No safe live websocket/chat preview or protected tenant-specific CRM
  data runtime; runtime serves one bot per process.
- No signed OCI release proven, vulnerability scan or image attestation.
- No managed secret KMS worker, revocation propagation, independent
  provider price quote, workspace quota enforcement, live reconciliation,
  webhook cutover, rollout/rollback or actual Telegram E2E test.
- `/health` does not check Bot API or prove message delivery.
- The public webhook verifies the Telegram secret header, but its security
  also depends on protecting the secret and ingress/proxy configuration.

**Before mass-market release:** implement a durable Redis/PostgreSQL state
backend with update deduplication, constrained replica policy, isolation,
rate limiting and audit. Finish provider billing controls and deploy worker
reconciliation. Use OCI signed/reproducible artifacts with provenance.

## PR integration

This PR is stacked on Secure Release PR #35. Merge in order only after CI
and local acceptance. The full production deployment process remains gated
until external provider rights, costs, secrets and Telegram delivery can be
verified.

Railway supports Docker image sources:
- https://docs.railway.com/services
- https://docs.railway.com/deployments/reference
