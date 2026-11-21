# Telegram PostgreSQL transactional outbox (optional adapter)

The existing production `runtime/telegram/app.py` continues to use its SQLite `state.py` and **single-replica** contract. This package does **not** switch the webhook runtime to PostgreSQL and does not enable automatic outbound delivery.

The isolated adapter `postgres_state.py` uses a dedicated managed PostgreSQL database with tables `omni_telegram_dialogues`, `omni_telegram_update_receipts`, and `omni_telegram_outbox`. It stages dialogue mutations and outbound commands in one transaction. The `outbox.py` sender is **manual opt-in**, marks an item claimed before contacting Telegram, and never blindly retries an ambiguous send. It is not exactly-once delivery; operator reconciliation is mandatory after ambiguous outcomes.

**Do not use this sender against a bot still delivering replies directly from its webhook handler.** To enable the PostgreSQL path, a separate cutover must wire inbound webhook handling to `PostgresStateStore.process`, stage all replies, deploy an isolated outbox worker, and validate a disposable PostgreSQL database and end-to-end Telegram delivery. Never run both delivery paths for the same bot instance.

Use `OMNI_TEST_RUNTIME_POSTGRES_URL` pointing to a **disposable test database** to run `pytest tests/test_telegram_postgres_state.py tests/test_telegram_outbox.py`. The tests skip when it is absent. Do not set this variable to production Neon. The sender requires explicit `--send-once` and its documented environment gate.

Source provenance: selectively adapted from legacy PR #38. Existing SQLite production tests and application entry point are intentionally unchanged.
