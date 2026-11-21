# Telegram Runtime · Railway staging acceptance

This release adds **production guardrails**, not automatic deployment. Do not
claim a bot is online before Telegram end-to-end acceptance succeeds.

## Where to go

1. Open the OmniFactory repository → **Pull requests** → the runtime PR → **Checks**.
2. After merging, open Railway → your **staging project** → **New Service** →
   **GitHub Repo** → `BondarevEugene/Personal_Web_Spase`.
3. In the service settings, leave the **Root Directory** empty (Docker build
   context is the repository root). Set **Config as Code** path to
   `/runtime/telegram/railway.json`. Confirm Railway resolves the Dockerfile
   `runtime/telegram/Dockerfile`.
4. Add a persistent Railway **Volume** mounted at `/data`. The SQLite file
   must survive deploys. Configure one replica and one worker only.
5. In **Variables**, set the following **privately** (never in Git or chat):
   - `BOT_TOKEN`: dedicated staging BotFather token
   - `TELEGRAM_WEBHOOK_SECRET`: random 32–128 alphanumeric/underscore/hyphen characters
   - `OMNI_SCENARIO_BASE64`: encoded validated scenario.json
   - `OMNI_STATE_SQLITE_PATH=/data/dialogues.sqlite3`
   - `OMNI_RUNTIME_PRODUCTION=1`
   - `OMNI_RUNTIME_BOOT=1` (already set in Docker image)
   - `WEB_CONCURRENCY=1`
6. Deploy and inspect Railway → **Deployments** → logs. Visit
   `https://YOUR-STAGING-DOMAIN/health` and `/ready`. Both endpoints
   prove only process and storage health, **not** Telegram delivery.
7. In a trusted operator environment, register the HTTPS URL
   `https://YOUR-STAGING-DOMAIN/telegram/webhook` via Telegram `setWebhook`,
   supplying the configured `secret_token`. Do not expose the token in logs.
8. In Telegram, open the **staging bot**, send `/start`, follow every branch,
   restart Railway mid-dialogue, verify state restoration, and retry a previously
   delivered `update_id` in a controlled integration test.
9. Inspect Railway logs, `/ready`, and Telegram `getWebhookInfo` for
   errors. Only after these tests pass mark delivery as verified.

## Reliability boundaries

The SQLite receipt table now distinguishes `processing` and `done`. A
processing update abandoned for 300 seconds may be retried; a completed update
is deduplicated. If the process crashes **after sending a Telegram message but
before marking the receipt done**, the retry may send it again. This is
**at-least-once** processing, not exactly-once Telegram delivery.

The in-process lock and SQLite database do **not** support multiple Railway
replicas. Do not increase replica count or workers. An in-flight processing
lease may be reclaimed while the original request is still running if it
exceeds 300 seconds; monitor for this condition. Production mode refuses to
start without an absolute SQLite path. Mount a durable volume, not ephemeral
container storage. Configure backups and restore tests before customer traffic.

**No Railway deployment, webhook registration, or live Telegram test is
performed by this PR.**
