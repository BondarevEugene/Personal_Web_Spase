"""Read-only PostgreSQL runtime operational diagnostics.

Only aggregate counts and ages are returned. Never expose chat IDs, message
bodies, bot credentials or user-specific dialogue state in diagnostics.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os

try:
    from runtime.telegram.postgres_state import PostgresStateStore
except ModuleNotFoundError:
    from postgres_state import PostgresStateStore


async def snapshot(store: PostgresStateStore, *, stale_seconds: int = 300) -> dict:
    if not 30 <= stale_seconds <= 86400:
        raise ValueError("stale_seconds must be between 30 and 86400")
    async with store.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT status, count(*) AS total, "
            "count(*) FILTER (WHERE updated_at < now() - ($2 * interval '1 second')) AS stale "
            "FROM omni_telegram_outbox WHERE bot_instance_id=$1 GROUP BY status",
            store.bot_instance_id, stale_seconds,
        )
        receipt_rows = await conn.fetch(
            "SELECT status, count(*) AS total, "
            "count(*) FILTER (WHERE updated_at < now() - ($2 * interval '1 second')) AS stale "
            "FROM omni_telegram_update_receipts WHERE bot_instance_id=$1 GROUP BY status",
            store.bot_instance_id, stale_seconds,
        )
    outbox = {r["status"]: {"total": r["total"], "stale": r["stale"]} for r in rows}
    receipts = {r["status"]: {"total": r["total"], "stale": r["stale"]} for r in receipt_rows}
    blocked = sum(outbox.get(status, {}).get("total", 0)
                  for status in ("claimed", "needs_reconciliation"))
    blocked += receipts.get("needs_reconciliation", {}).get("total", 0)
    return {
        "healthy": blocked == 0,
        "stale_seconds": stale_seconds,
        "outbox": outbox,
        "receipts": receipts,
        "requires_operator_review": blocked > 0,
    }


async def run_diagnostics(stale_seconds: int) -> int:
    store = await PostgresStateStore.connect(
        os.getenv("OMNI_RUNTIME_DATABASE_URL", ""),
        os.getenv("OMNI_BOT_INSTANCE_ID", ""),
    )
    try:
        result = await snapshot(store, stale_seconds=stale_seconds)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["healthy"] else 2
    finally:
        await store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Telegram runtime diagnostics")
    parser.add_argument("--stale-seconds", type=int, default=300)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_diagnostics(args.stale_seconds)))


if __name__ == "__main__":
    main()
