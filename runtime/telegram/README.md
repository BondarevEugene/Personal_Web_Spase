# OmniFactory Telegram Webhook Runtime v1

Build from **repository root**:

```bash
docker build -f runtime/telegram/Dockerfile -t omni-telegram-runtime:test .
```

Requires the deployment operator to inject three variables from a dedicated
secret/config system, **not** the visual builder JSON or Git:

- `BOT_TOKEN`: BotFather token. Never place it in an image layer.
- `TELEGRAM_WEBHOOK_SECRET`: random 32–128 char Telegram secret token.
- `OMNI_SCENARIO_BASE64`: UTF-8 scenario.json, base64 encoded, max 200 KiB.
- `PORT`: optional listening port (defaults to 8000).

`GET /health` reports **process_ready**, not end-to-end Telegram reachability.
`POST /telegram/webhook` verifies the Telegram
`X-Telegram-Bot-Api-Secret-Token` header, with bounded request sizes.
Use HTTPS termination and configure Telegram's `setWebhook` separately
using your trusted deployment operator; it is deliberately not automatic.

**Important limits:** dialogue state is in memory; no distributed lock,
durable cursor, update deduplication, delayed queues, automatic bot token
rotation or post-deploy cutover verification. Run one replica only in isolated
development. Reboots lose conversation state. A production release still needs
PostgreSQL/Redis state, auditing, idempotent update receipts and cost controls.

Do not deploy this container to real clients until it passes threat modelling,
reproducible image/SBOM/vulnerability checks and full Telegram E2E testing.


## PostgreSQL durable dialogue state (next phase)

Production runtime now requires `OMNI_RUNTIME_DATABASE_URL` and `OMNI_BOT_INSTANCE_ID`.
All dialogue and inbound update records are namespaced by the bot instance ID.
Apply schema separately using `runtime/telegram/state.py` DDL before starting,
or explicitly opt in with `OMNI_RUNTIME_BOOTSTRAP_SCHEMA=1` **on a test database only**.
Missing PostgreSQL makes runtime startup fail closed; no fallback in-memory mode in production.

An inbound update is marked claimed before any outgoing Telegram API call;
repeated updates are suppressed. Failed or interrupted updates have uncertain
external side effects and are quarantined rather than blindly replayed.
This is **not exactly-once delivery** and still uses a single replica.
