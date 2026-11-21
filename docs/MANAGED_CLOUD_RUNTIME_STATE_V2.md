# OmniFactory Runtime State Engine v2 — PostgreSQL

## Purpose

Keep Telegram conversation position and variables across runtime restarts and
guard inbound Telegram `update_id` processing against retries. Designed for
one isolated bot process per service and a **separate runtime database**.

This is a milestone toward Managed Cloud, not automatic paid deployment.

## Architecture

- `runtime/telegram/state.py`: two PostgreSQL tables:
  `omni_telegram_dialogues` keyed by `bot_instance_id/chat_id/user_id`
  and `omni_telegram_update_receipts` keyed by
  `bot_instance_id/update_id`.
- `runtime/telegram/app.py`: each incoming update runs inside its own
  ContextVar-backed dialogue snapshot; no cross-request mutable cursor.
- A receipt is **committed before any Telegram send**. Redis is not required.
- A PostgreSQL advisory lock serializes changes for one bot/chat/user.
- Success commits the dialogue and sets the receipt to `processed`.
- Repeated processed update IDs return `duplicate` without rerunning.
- A failure after claim is marked `needs_reconciliation`. A crash while
  handling leaves `processing`; both statuses block blind replay.
- The restricted `GET /internal/state` endpoint gives **counts only**,
  guarded by `X-Omni-Operator-Token` and a configured
  `OMNI_RUNTIME_OBSERVABILITY_TOKEN`. It has no chat content or user IDs.

## Runtime variables

| Name | Required | Meaning |
| --- | --- | --- |
| `BOT_TOKEN` | Yes, secret | BotFather token |
| `TELEGRAM_WEBHOOK_SECRET` | Yes, secret | Telegram webhook secret header |
| `OMNI_SCENARIO_BASE64` | Yes, config | Validated bounded graph |
| `OMNI_RUNTIME_DATABASE_URL` | Yes, secret | Dedicated runtime PostgreSQL URL |
| `OMNI_BOT_INSTANCE_ID` | Yes, config | Stable unique bot instance ID, 8–80 safe chars |
| `OMNI_RUNTIME_OBSERVABILITY_TOKEN` | Recommended, secret | Restricted runtime counters |
| `OMNI_RUNTIME_BOOTSTRAP_SCHEMA` | Test only | Set to `1` to bootstrap the two tables in a throwaway DB |
| `PORT` | Optional | HTTP listening port, default 8000 |

**Production startup fails closed without PostgreSQL**, unlike the unit-test
`build_runtime(require_state=False)` path.

Never use production Neon credentials for schema bootstrap. Run DDL from
`runtime/telegram/state.py` as an operator-controlled migration on a
**separate runtime database** before launch. Make a backup first. Keep
`OMNI_RUNTIME_BOOTSTRAP_SCHEMA` unset in production.

## A crucial delivery guarantee boundary

**This design does not guarantee exactly-once outgoing messages.**

If Telegram receives a send and PostgreSQL transaction later aborts, the
actual delivery outcome is ambiguous. We quarantine the receipt rather than
automatically retry the send (which could duplicate it). If the process dies
after claim, the receipt may remain `processing` and also blocks retries.

A quarantined update requires manual reconciliation; there is no built-in
operator resolution/replay endpoint. Telegram may retry and receive HTTP 503,
but the update will not automatically execute again. That prioritizes
avoiding duplicate side effects over guaranteed delivery. It is not yet
suitable for critical, paid, or high-throughput customer workflows.

**Next:** an isolated transactional outbox with separate bounded sender,
persisted command IDs, reconciliation and business-aware retry policy. The
outbox can guarantee state transitions and enqueue operations, but exact
external delivery still depends on the messaging provider's idempotency
semantics. Telegram `sendMessage` does not expose a general caller-defined
idempotency key.

## Operational caveats

- Keep a single runtime replica per bot for now, even with advisory locks.
- A transaction holds the dialogue lock while calling Telegram; slow or
  unavailable Telegram can hold an active DB connection. Keep timeouts and
  one-replica limits conservative.
- Dialogue variables may include personal customer information. Keep runtime
  DB access restricted, backups encrypted, and define user-data
  retention/deletion policies before real customer deployment.
- No automatic receipt cleanup yet. Do not delete uncertain receipts without
  documented reconciliation and retention policy.
- No live Railway mutations, Telegram setWebhook cutover, cost approvals,
  Redis, payment effects, signed OCI artifacts or end-to-end Telegram
  delivery in this PR.
- The HTTP `/health` checks the local process and PostgreSQL connection,
  not Telegram delivery or webhook health.

## Local development on Windows PowerShell

You already installed `aiogram==3.22.0` into `.venv-clean`. That command
also downgraded `pydantic`, `aiohttp` and other dependencies. Separate
runtime and portal environments to avoid conflicts.

```powershell
# Inspect the portal environment without modifying it:
.\.venv-clean\Scripts\python.exe -m pip check

# Create an independent runtime environment:
py -3.12 -m venv .venv-runtime
.\.venv-runtime\Scripts\python.exe -m pip install -r runtime/telegram/requirements.txt

# Portal/regression tests remain under the portal environment:
.\.venv-clean\Scripts\python.exe -m pytest tests/test_telegram_runtime_v1.py tests/test_secure_release.py -q --tb=short

# Build a separate runtime image from the repository root:
docker build -f runtime/telegram/Dockerfile -t omnifactory-runtime:durable .
```

For PostgreSQL integration tests, set
`OMNI_TEST_RUNTIME_POSTGRES_URL` to a **disposable test DB only**.
Never use the live Neon instance; tests create state tables and write data.
GitHub Actions includes its own temporary PostgreSQL service and executes
these tests automatically.

## Future Bot Lab integration

Future release workers will push actual provider IDs, runtime heartbeat,
quarantine/lag counts and deployment diagnostics into the CRM through
authenticated service-to-service channels. Do **not** expose
`/internal/state` publicly, embed operator tokens in JavaScript, or allow
client-supplied URLs to access it.

A bot will only be marked `online` after Railway deployment status,
runtime `/health`, Telegram webhook configuration and a controlled
delivery check have all been verified.
