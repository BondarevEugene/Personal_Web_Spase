"""Non-retrying Telegram outbox sender for one isolated bot instance.

Safe by default: the dispatcher needs an explicit runtime setting AND CLI
opt-in to send. Each command changes from pending to claimed and commits
before invoking Telegram. Crashes after claim remain ambiguous and are
never auto-retried; operator reconciliation is mandatory.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from typing import Awaitable, Callable

import asyncpg

from state import INSTANCE_ID, PostgresStateStore


@dataclass(frozen=True)
class Command:
    bot_instance_id: str
    update_id: int
    seq: int
    chat_id: int
    method: str
    payload: dict


async def claim_one(store: PostgresStateStore) -> Command | None:
    async with store.pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT bot_instance_id,update_id,seq,chat_id,method,payload_json "
                "FROM omni_telegram_outbox "
                "WHERE bot_instance_id=$1 AND status='pending' "
                "AND NOT EXISTS (SELECT 1 FROM omni_telegram_outbox earlier "
                "WHERE earlier.bot_instance_id=omni_telegram_outbox.bot_instance_id "
                "AND earlier.update_id=omni_telegram_outbox.update_id "
                "AND earlier.seq<omni_telegram_outbox.seq AND earlier.status<>'sent') "
                "ORDER BY update_id,seq FOR UPDATE SKIP LOCKED LIMIT 1",
                store.bot_instance_id)
            if row is None:
                return None
            # Do not deliver a later action before an earlier action's
            # outcome is known: maintain per-update command ordering.
            blocked = await conn.fetchval(
                "SELECT 1 FROM omni_telegram_outbox WHERE bot_instance_id=$1 "
                "AND update_id=$2 AND seq<$3 AND status<>'sent' LIMIT 1",
                store.bot_instance_id, row["update_id"], row["seq"])
            if blocked:
                return None
            await conn.execute(
                "UPDATE omni_telegram_outbox SET status='claimed',"
                "claimed_at=now(),updated_at=now() WHERE bot_instance_id=$1 "
                "AND update_id=$2 AND seq=$3 AND status='pending'",
                store.bot_instance_id, row["update_id"], row["seq"])
            payload = row["payload_json"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            return Command(
                bot_instance_id=store.bot_instance_id,
                update_id=row["update_id"], seq=row["seq"], chat_id=row["chat_id"],
                method=row["method"], payload=payload,
            )


async def finish(store: PostgresStateStore, item: Command, *, success: bool) -> None:
    async with store.pool.acquire() as conn:
        await conn.execute(
            "UPDATE omni_telegram_outbox SET status=$4,"
            "sent_at=CASE WHEN $4='sent' THEN now() ELSE NULL END,"
            "updated_at=now() WHERE bot_instance_id=$1 AND update_id=$2 "
            "AND seq=$3 AND status='claimed'",
            item.bot_instance_id, item.update_id, item.seq,
            "sent" if success else "needs_reconciliation")


async def dispatch_once(
    store: PostgresStateStore,
    sender: Callable[[Command], Awaitable[None]],
) -> str:
    item = await claim_one(store)
    if item is None:
        return "empty"
    try:
        if item.method != "send_message":
            raise ValueError("Unrecognized outbox method")
        text = item.payload.get("text") if isinstance(item.payload, dict) else None
        if not isinstance(text, str) or not 1 <= len(text) <= 4000:
            raise ValueError("Invalid outbox message")
        await sender(item)
    except Exception:
        await finish(store, item, success=False)
        # Do not leak raw Bot API/network errors (possibly containing tokens).
        return "needs_reconciliation"
    await finish(store, item, success=True)
    return "sent"


async def counters(store: PostgresStateStore) -> dict[str, int]:
    async with store.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT status,count(*) AS n FROM omni_telegram_outbox "
            "WHERE bot_instance_id=$1 GROUP BY status", store.bot_instance_id)
        return {row["status"]: row["n"] for row in rows}


async def serve_one():
    if os.getenv("OMNI_OUTBOX_SEND_ENABLED") != "1":
        raise RuntimeError("Outbox sending disabled. Explicit operator approval required.")
    token = os.getenv("BOT_TOKEN", "")
    from aiogram import Bot
    from app import TOKEN_PATTERN
    if not TOKEN_PATTERN.fullmatch(token):
        raise RuntimeError("Invalid Telegram bot credential")
    store = await PostgresStateStore.connect(
        os.getenv("OMNI_RUNTIME_DATABASE_URL", ""),
        os.getenv("OMNI_BOT_INSTANCE_ID", ""))
    bot = Bot(token)
    try:
        async def send(item: Command):
            await bot.send_message(item.chat_id, item.payload["text"])
        return await dispatch_once(store, send)
    finally:
        await bot.session.close()
        await store.close()


def main():
    parser = argparse.ArgumentParser(description="Explicitly run ONE outbox delivery")
    parser.add_argument("--send-once", action="store_true", required=True)
    parser.parse_args()
    print(asyncio.run(serve_one()))


if __name__ == "__main__":
    main()
