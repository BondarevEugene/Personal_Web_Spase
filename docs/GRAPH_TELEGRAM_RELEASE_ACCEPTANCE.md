# Graph Studio · Telegram ZIP release contract

This release gate checks **the actual bytes** of each generated bot ZIP before
the download is returned. It validates ZIP membership, bounded sizes, Python
syntax, the standalone webhook-runtime scenario contract, dependency declaration,
persistence documentation and placeholder-only BotFather credentials.

## Offline acceptance

```powershell
python -m pytest -q tests/test_export_contract.py tests/test_builder_export_zip_acceptance.py
python scripts/verify_telegram_export.py .\omnifactory_telegram_bot.zip
```

A successful report means **archive structure, Python syntax and scenario
compatibility passed**. It does **not** mean Telegram delivery, hosting, webhook
registration, real BotFather token validation or Railway deployment succeeded.

## Manual production acceptance checklist

1. Download the ZIP from a saved scenario that passes Graph Studio preflight.
2. Verify the ZIP offline with the command above.
3. Extract it into an isolated environment and install its pinned-major aiogram dependency.
4. Set `BOT_TOKEN` in environment variables; never commit a real token.
5. Configure a persistent `OMNI_STATE_DB` path, single bot instance and backups.
6. Start the generated bot and test /start, every button, input, variable and branch with a dedicated test Telegram account.
7. Restart the process mid-dialogue and confirm cursor and variables survive.
8. Verify invalid/stale callback handling, provider error reporting and restart behavior.
9. Only then describe the bot as deployed and available.

The separate `runtime/telegram` webhook service has its own security and
deployment model; passing this ZIP contract does not provision that service.
