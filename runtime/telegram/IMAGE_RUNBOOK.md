# Telegram runtime · production image contract

The image must package `app.py`, `scenario.py`, `state.py` and `maintenance.py`. The runtime cannot start with persistence enabled if `state.py` is missing.

Build from the **repository root**:

```bash
docker build -f runtime/telegram/Dockerfile -t omnifactory-telegram-runtime:local .
```

Configure `BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `OMNI_SCENARIO_BASE64` and `OMNI_STATE_SQLITE_PATH=/data/state.db` through your deployment secret manager, not the image or Git repository. Attach a persistent volume at `/data`; its directory is owned by UID 10001. The image is intended for **one replica**.

Run `GET /health` for process health and `GET /ready` for local database integrity. Neither proves Telegram webhook registration or message delivery.

The webhook now serializes updates for the same chat/user within a single process. This reduces lost state under concurrent requests, but it is **not distributed locking** and does not guarantee exactly-once external sends after a crash. Provider-side reconciliation and real delivery tests remain prerequisites to production claims.
