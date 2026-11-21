# Telegram Runtime — Railway staging acceptance

This configuration prepares **staging**, not production certification. It does not by itself implement crash recovery or verify Telegram delivery.

1. In Railway create a staging service from this repository. Keep the repository root as the Docker build context and set Config as Code to `/runtime/telegram/railway.json`.
2. Mount a persistent volume at `/data`; use **one replica and one worker**. SQLite dialogue state is not safe for distributed replicas.
3. Set private environment variables `BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `OMNI_SCENARIO_BASE64` and `OMNI_STATE_SQLITE_PATH=/data/dialogues.sqlite3`. Never commit tokens.
4. Verify that the deployed runtime actually implements `/ready` and that it reports durable storage health. A healthcheck is not evidence of Telegram delivery.
5. Manually register the Telegram webhook with the secret token. Test `/start`, all dialogue branches, restarts, duplicate `update_id` delivery and failed-send retries.
6. Check logs and Telegram `getWebhookInfo`; only mark staging accepted after real end-to-end tests.

## Known reliability gap

The baseline SQLite store records update IDs before successful delivery. A crash between claiming an update and completing its side effects may suppress retries. **The production receipt lifecycle from PR #140 still needs integration and regression tests**; do not claim at-least-once recovery or exactly-once Telegram delivery.

No Railway deployment or webhook registration is performed by this PR.
