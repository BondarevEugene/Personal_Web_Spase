# OmniFactory Runtime v3 — Transactional Outbox Foundation

## What is actually implemented

This phase introduces a PostgreSQL **transactional staging and dispatch
primitive**, distinct from full integration into the Telegram scenario
interpreter.

- `Conversation.queue_message(chat_id, text)` stages bounded outgoing
  `send_message` commands (max 50 per update).
- `PostgresStateStore.process` atomically commits staged outgoing commands
  with the conversation state and inbound update receipt.
- `omni_telegram_outbox` has a unique `(bot_instance_id,update_id,seq)`
  command key. Foreign key ties it to the inbound receipt. Commands are
  ordered and isolated per bot.
- `runtime/telegram/outbox.py` offers a one-at-a-time claim/dispatch
  primitive using `FOR UPDATE SKIP LOCKED`. It commits `claimed`
  **before** calling Telegram. Success records `sent`. Failure records
  `needs_reconciliation`. Stale claimed commands remain blocked.
- Sending is **disabled by default** and can only run with both
  `OMNI_OUTBOX_SEND_ENABLED=1` and an explicit `--send-once` operator command.
- Real PostgreSQL acceptance tests verify atomic staging, ordering,
  duplicate suppression, claim isolation, sender uncertainty and rollback.
  CI builds the Docker image with the outbox component included.

### Extremely important limitation

The current `runtime/telegram/app.py` Graph Studio interpreter still calls
`bot.send_message/send_photo/send_document` directly. It has **not yet been
migrated** to stage every side effect into the outbox.

This PR therefore delivers the **outbox core**, not an end-to-end outbox
guarantee for all live bot dialogue paths. Before enabling real traffic,
refactor all outbound operations (including callback acknowledgements,
choices, photos and documents) to append typed commands rather than
perform external calls in the inbound transaction. Do not enable the
standalone sender against a real production runtime before that work.

Telegram Bot API lacks universal per-request idempotency keys. Even with
outbox, losing the acknowledgment after a successful send creates an
unknown outcome. Never automatically retry `claimed` or
`needs_reconciliation` without explicit provider-specific reconciliation
and operator approval.

## User security

- Commands are scoped to `bot_instance_id`, which is generated/authorized
  by the deployment control plane, not a client-supplied arbitrary ID.
- Outbox `payload_json` can contain end-user message content and is therefore
  sensitive personal data. Encrypt backups and enforce access restrictions.
- Never return raw payloads to a global administrator or a different tenant.
  Build tenant-specific, permission-checked Bot Lab counters in a separate
  future PR. This phase has no public outbox status API.
- Do not put Telegram tokens, database passwords or webhook secrets in
  scenario JSON or outbound command payloads.
- Dedicate a PostgreSQL database/schema to runtime state. Apply its DDL from
  `runtime/telegram/state.py` only in controlled development/test migration.
  Do not enable `OMNI_RUNTIME_BOOTSTRAP_SCHEMA` on production.

## Windows/PyCharm acceptance

```powershell
git fetch origin
git switch -c feat/runtime-transactional-outbox-20261114 --track origin/feat/runtime-transactional-outbox-20261114

# Portal checks, no dependency upgrades:
.\.venv-clean\Scripts\python.exe -m pip check

# Runtime-specific dependencies belong in their own venv:
.\.venv-runtime\Scripts\python.exe -m pip install -r runtime/telegram/requirements.txt
.\.venv-runtime\Scripts\python.exe -m pytest tests/test_telegram_outbox.py -q

# Docker build from repo root:
docker build -f runtime/telegram/Dockerfile -t omni-runtime:outbox-dev .
```

The PostgreSQL tests need `OMNI_TEST_RUNTIME_POSTGRES_URL` pointing to a
**disposable** test database; without it, DB-dependent tests are skipped.
Github Actions supplies an isolated PostgreSQL 16 service and executes them.

## Next work

1. Replace interpreter's direct Telegram calls with staged typed commands.
2. Extend outbox for reply_markup, callback answer, photo/document, and
   other supported builder nodes.
3. Add delivery worker safety guard, operator reconciliation, quarantine
   UI, alerting and rate limiting.
4. Implement lifecycle status and cost metrics in Bot Lab with actual
   tenant-scoped evidence.
5. Only then enable verified paid Railway provisioning and Telegram cutover.
