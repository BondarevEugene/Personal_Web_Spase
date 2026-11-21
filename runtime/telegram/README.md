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

**Persistence and staging:** optional SQLite-backed dialogue cursors and
update receipts are implemented for a single replica. Set
`OMNI_STATE_SQLITE_PATH` to a persistent volume path. With
`OMNI_RUNTIME_PRODUCTION=1`, startup rejects a missing or relative SQLite
path and rejects `WEB_CONCURRENCY` other than 1. The update receipt
distinguishes in-flight and completed events; abandoned in-flight events can
be retried after five minutes. Telegram delivery remains at-least-once,
not exactly-once.

See [RAILWAY_STAGING.md](RAILWAY_STAGING.md) for step-by-step Railway
configuration, verification endpoints and Telegram E2E acceptance.

Do not deploy to real clients before threat modelling, image provenance,
backups and successful live Telegram testing.
