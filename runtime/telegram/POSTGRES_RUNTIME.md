# Telegram Runtime: PostgreSQL transactional delivery (opt-in)

This release introduces an **explicit opt-in** storage mode. It does not migrate
existing SQLite dialogue state, and does not automatically enable delivery.

## Configuration

Set `OMNI_RUNTIME_STORAGE=postgresql`, `OMNI_RUNTIME_DATABASE_URL`
(dedicated runtime PostgreSQL/Neon DSN), `OMNI_BOT_INSTANCE_ID` (8–80 safe
characters), plus existing `BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`,
`OMNI_SCENARIO_BASE64`, `OMNI_RUNTIME_PRODUCTION=1`.
Do not share the production runtime DB with test suites.

Bootstrap the tables from a controlled one-time administrative process using
`PostgresStateStore.connect(dsn, instance_id, bootstrap_schema=True)`.
The runtime **does not** create tables at boot.

The webhook commits dialogue state, receipt and outgoing text commands in a
single PostgreSQL transaction, then returns 200. A separate outbox worker
delivers commands. Until a worker is configured, commands remain pending.

`OMNI_OUTBOX_SEND_ENABLED=1 python -m runtime.telegram.outbox --send-once`
is a deliberately explicit, **single-command** sender, not a background worker.
Run under a trusted operator scheduler only after verifying the bot token,
instance ID and pending queue. It will not retry ambiguous sends.

## Current scope and safety

- Text messages, text-based numbered choices, input, conditions, variables,
  and end nodes are supported. Inline callback buttons, media and document
  sends are **not** supported in PostgreSQL mode; unsupported operations fail
  closed. Use SQLite mode until the scenario has been adapted and tested.
- `GET /health` checks the process, `GET /ready` checks database connectivity,
  and `GET /outbox/health` returns status counts, **not** delivery verification.
- Duplicate updates are deduplicated by bot instance and update ID.
- A crash or exception before commit leaves a receipt needing reconciliation.
  A crash after outbox claim may mean Telegram delivered the message: claimed
  rows are **never** automatically requeued.
- Reconcile `needs_reconciliation` and stale `claimed` rows manually with
  Telegram-side evidence before changing state. Telegram Bot API provides no
  exactly-once send guarantee.
- Do not switch a live bot from SQLite to PostgreSQL without a planned
  cutover, state migration and Telegram end-to-end verification.

## Acceptance

`python -m pytest -q tests/test_telegram_postgres_webhook.py`

For real PostgreSQL integration, set `OMNI_TEST_RUNTIME_POSTGRES_URL` to a
disposable database and run `tests/test_telegram_postgres_state.py` and
`tests/test_telegram_outbox.py`. Without the variable, those tests skip;
a skip is **not** proof of PostgreSQL production readiness.
