"""PostgreSQL-backed Telegram runtime state and inbound-update receipt ledger.

Designed for a dedicated Telegram bot runtime (not OmniFactory's portal DB).
An update is claimed *before* any outbound Telegram call. On failure its
outcome is uncertain and is quarantined instead of blindly replayed.
This prevents automatic duplicate sends but is NOT guaranteed exactly-once
delivery. An outbox can now atomically stage commands; outbound delivery still needs reconciliation.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Awaitable, Callable, TypeVar

import asyncpg

T = TypeVar("T")
INSTANCE_ID = re.compile(r"^[A-Za-z0-9_-]{8,80}$")
DDL = """
CREATE TABLE IF NOT EXISTS omni_telegram_dialogues (
    bot_instance_id varchar(80) NOT NULL,
    chat_id bigint NOT NULL,
    user_id bigint NOT NULL,
    cursor varchar(40),
    values_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(bot_instance_id, chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS omni_telegram_update_receipts (
    bot_instance_id varchar(80) NOT NULL,
    update_id bigint NOT NULL,
    status varchar(28) NOT NULL
        CHECK (status IN ('processing', 'processed', 'needs_reconciliation')),
    error_code varchar(48),
    received_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(bot_instance_id, update_id)
);
CREATE INDEX IF NOT EXISTS ix_omni_telegram_update_receipts_status
    ON omni_telegram_update_receipts(bot_instance_id, status, received_at);
CREATE TABLE IF NOT EXISTS omni_telegram_outbox (
    bot_instance_id varchar(80) NOT NULL,
    update_id bigint NOT NULL,
    seq smallint NOT NULL,
    chat_id bigint NOT NULL,
    method varchar(30) NOT NULL CHECK (method IN ('send_message')),
    payload_json jsonb NOT NULL,
    status varchar(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','claimed','sent','needs_reconciliation')),
    claimed_at timestamptz,
    sent_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(bot_instance_id, update_id, seq),
    FOREIGN KEY(bot_instance_id, update_id)
        REFERENCES omni_telegram_update_receipts(bot_instance_id, update_id),
    CHECK (seq BETWEEN 0 AND 49)
);
CREATE INDEX IF NOT EXISTS ix_omni_telegram_outbox_pending
    ON omni_telegram_outbox (bot_instance_id, status, update_id, seq);
"""


class StoreUnavailable(RuntimeError):
    pass


class AmbiguousDelivery(RuntimeError):
    """A Telegram side effect might have happened; do not replay automatically."""


@dataclass
class Conversation:
    cursor: str | None
    values: dict[str, str]
    outbox: list[dict] = field(default_factory=list)

    def queue_message(self, chat_id: int, text: str) -> None:
        if not isinstance(chat_id, int) or not isinstance(text, str) or not 1 <= len(text) <= 4000:
            raise ValueError("Invalid outgoing Telegram text")
        if len(self.outbox) >= 50:
            raise ValueError("Too many outbound operations in one update")
        self.outbox.append({"chat_id": chat_id, "method": "send_message", "text": text})


class PostgresStateStore:
    def __init__(self, pool: asyncpg.Pool, bot_instance_id: str):
        if not INSTANCE_ID.fullmatch(bot_instance_id):
            raise ValueError("Invalid bot instance ID")
        self.pool = pool
        self.bot_instance_id = bot_instance_id

    @classmethod
    async def connect(cls, dsn: str, bot_instance_id: str,
                      *, bootstrap_schema: bool = False) -> "PostgresStateStore":
        if not dsn or not dsn.startswith(("postgresql://", "postgres://")):
            raise StoreUnavailable("PostgreSQL runtime DSN required")
        if not INSTANCE_ID.fullmatch(bot_instance_id):
            raise StoreUnavailable("Valid isolated bot instance ID required")
        try:
            pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5,
                                             command_timeout=12, timeout=10)
            async with pool.acquire() as conn:
                if bootstrap_schema:
                    await conn.execute(DDL)
                else:
                    await conn.fetchval("SELECT count(*) FROM omni_telegram_dialogues")
                    await conn.fetchval("SELECT count(*) FROM omni_telegram_update_receipts")
                    await conn.fetchval("SELECT count(*) FROM omni_telegram_outbox")
            return cls(pool, bot_instance_id)
        except Exception as exc:
            if "pool" in locals():
                await pool.close()
            raise StoreUnavailable("Telegram runtime storage unavailable or schema missing") from exc

    async def close(self):
        await self.pool.close()

    def _lock_key(self, chat_id: int, user_id: int) -> int:
        material = f"{self.bot_instance_id}:{chat_id}:{user_id}".encode()
        return int.from_bytes(hashlib.sha256(material).digest()[:8], "big", signed=True)

    async def receipt_status(self, update_id: int) -> str | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT status FROM omni_telegram_update_receipts "
                "WHERE bot_instance_id=$1 AND update_id=$2",
                self.bot_instance_id, update_id)

    async def process(
        self, update_id: int, chat_id: int, user_id: int,
        run: Callable[[Conversation], Awaitable[T]],
    ) -> tuple[str, T | None]:
        """Returns processed/duplicate; quarantines uncertain external sends.

        Telegram may deliver duplicates. One receipt is inserted first,
        committed, then the dialogue is acquired via a PG advisory lock.
        A failed/crashed attempt remains blocked; no automatic replay.
        """
        if not isinstance(update_id, int) or update_id < 0:
            raise ValueError("Invalid Telegram update ID")
        async with self.pool.acquire() as conn:
            added = await conn.fetchval(
                "INSERT INTO omni_telegram_update_receipts "
                "(bot_instance_id, update_id, status) VALUES ($1,$2,'processing') "
                "ON CONFLICT DO NOTHING RETURNING update_id",
                self.bot_instance_id, update_id)
            if added is None:
                current = await self.receipt_status(update_id)
                if current == "processed":
                    return "duplicate", None
                raise AmbiguousDelivery("Update already claimed; manual reconciliation required")
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Serialize edits to a single conversation, even across
                    # instances. Never call Telegram outside this lock.
                    await conn.execute("SELECT pg_advisory_xact_lock($1)",
                                       self._lock_key(chat_id, user_id))
                    row = await conn.fetchrow(
                        "SELECT cursor, values_json FROM omni_telegram_dialogues "
                        "WHERE bot_instance_id=$1 AND chat_id=$2 AND user_id=$3",
                        self.bot_instance_id, chat_id, user_id)
                    raw = row["values_json"] if row else {}
                    vals = json.loads(raw) if isinstance(raw, str) else raw
                    if not isinstance(vals, dict):
                        raise StoreUnavailable("Invalid dialogue state")
                    state = Conversation(
                        cursor=row["cursor"] if row else None,
                        values={str(k): str(v) for k, v in vals.items()},
                    )
                    result = await run(state)
                    if len(state.values) > 40 or any(
                        len(k) > 40 or len(v) > 300 for k,v in state.values.items()
                    ):
                        raise StoreUnavailable("Conversation exceeded state quota")
                    await conn.execute(
                        "INSERT INTO omni_telegram_dialogues "
                        "(bot_instance_id,chat_id,user_id,cursor,values_json,updated_at) "
                        "VALUES ($1,$2,$3,$4,$5::jsonb,now()) "
                        "ON CONFLICT(bot_instance_id,chat_id,user_id) DO UPDATE "
                        "SET cursor=excluded.cursor, values_json=excluded.values_json,"
                        "updated_at=now()",
                        self.bot_instance_id, chat_id, user_id, state.cursor,
                        json.dumps(state.values, separators=(",", ":")))
                    for seq, action in enumerate(state.outbox):
                        await conn.execute(
                            "INSERT INTO omni_telegram_outbox "
                            "(bot_instance_id,update_id,seq,chat_id,method,payload_json,status) "
                            "VALUES ($1,$2,$3,$4,$5,$6::jsonb,'pending')",
                            self.bot_instance_id, update_id, seq, action["chat_id"],
                            action["method"], json.dumps({"text": action["text"]}))
                    await conn.execute(
                        "UPDATE omni_telegram_update_receipts "
                        "SET status='processed',updated_at=now() "
                        "WHERE bot_instance_id=$1 AND update_id=$2 AND status='processing'",
                        self.bot_instance_id, update_id)
                    return "processed", result
        except Exception:
            # Any Telegram calls made before failure have uncertain outcome.
            # Do not automatically replay the same update.
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE omni_telegram_update_receipts "
                    "SET status='needs_reconciliation', error_code='UNKNOWN_SEND_OUTCOME', "
                    "updated_at=now() WHERE bot_instance_id=$1 AND update_id=$2 "
                    "AND status='processing'",
                    self.bot_instance_id, update_id)
            raise AmbiguousDelivery("Telegram update outcome uncertain; operator action required") from None

    async def counts(self) -> dict[str, int]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT status, count(*) AS n FROM omni_telegram_update_receipts "
                "WHERE bot_instance_id=$1 GROUP BY status", self.bot_instance_id)
            return {row["status"]: row["n"] for row in rows}
