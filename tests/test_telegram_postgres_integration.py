"""Real PostgreSQL integration tests; CI provides a disposable database."""
import asyncio
import os
import uuid

import pytest

from runtime.telegram.outbox import claim_one, counters, finish
from runtime.telegram.postgres_diagnostics import snapshot
from runtime.telegram.postgres_state import (
    AmbiguousDelivery,
    PostgresStateStore,
)


def test_postgres_atomic_receipts_and_outbox():
    dsn = os.getenv("OMNI_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("OMNI_TEST_POSTGRES_DSN not configured")

    async def scenario():
        instance = "test_" + uuid.uuid4().hex
        store = await PostgresStateStore.connect(dsn, instance, bootstrap_schema=True)
        try:
            async def create(state):
                state.values["name"] = "Alex"
                state.cursor = "choice"
                state.queue_message(123, "Pick", {
                    "inline_keyboard": [[{"text": "Yes", "callback_data": "omni:choice:0"}]]
                })
                state.queue_action(123, "send_photo", {"photo": "telegram-file-id"})
                state.queue_action(123, "answer_callback_query", {
                    "callback_query_id": "callback-id"
                })

            status, _ = await store.process(9001, 123, 456, create)
            assert status == "processed"
            duplicate, _ = await store.process(9001, 123, 456, create)
            assert duplicate == "duplicate"
            counts = await counters(store)
            assert counts["pending"] == 3

            diag = await snapshot(store)
            assert diag["healthy"] is True
            assert diag["outbox"]["pending"]["total"] == 3

            first = await claim_one(store)
            assert first.method == "send_message"
            assert first.payload["reply_markup"]["inline_keyboard"][0][0]["text"] == "Yes"
            assert await claim_one(store) is None  # ordering blocks later commands
            await finish(store, first, success=True)
            second = await claim_one(store)
            assert second.method == "send_photo"
            await finish(store, second, success=True)
            third = await claim_one(store)
            assert third.method == "answer_callback_query"
            await finish(store, third, success=False)

            diag = await snapshot(store)
            assert diag["requires_operator_review"] is True
            assert diag["outbox"]["needs_reconciliation"]["total"] == 1
            assert await claim_one(store) is None

            async with store.pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT cursor, values_json FROM omni_telegram_dialogues "
                    "WHERE bot_instance_id=$1 AND chat_id=123 AND user_id=456", instance,
                )
                assert row["cursor"] == "choice"
                assert row["values_json"]["name"] == "Alex"
        finally:
            async with store.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM omni_telegram_outbox WHERE bot_instance_id=$1", instance
                )
                await conn.execute(
                    "DELETE FROM omni_telegram_update_receipts WHERE bot_instance_id=$1",
                    instance,
                )
                await conn.execute(
                    "DELETE FROM omni_telegram_dialogues WHERE bot_instance_id=$1", instance
                )
            await store.close()

    asyncio.run(scenario())


def test_postgres_failure_is_quarantined_without_partial_writes():
    dsn = os.getenv("OMNI_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("OMNI_TEST_POSTGRES_DSN not configured")

    async def scenario():
        instance = "test_" + uuid.uuid4().hex
        store = await PostgresStateStore.connect(dsn, instance, bootstrap_schema=True)
        try:
            async def failing(state):
                state.queue_message(123, "Should not be sent")
                raise ValueError("invalid scenario")

            with pytest.raises(AmbiguousDelivery):
                await store.process(9002, 123, 456, failing)
            assert await store.receipt_status(9002) == "needs_reconciliation"
            assert await counters(store) == {}
            with pytest.raises(AmbiguousDelivery):
                await store.process(9002, 123, 456, failing)
        finally:
            async with store.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM omni_telegram_outbox WHERE bot_instance_id=$1", instance
                )
                await conn.execute(
                    "DELETE FROM omni_telegram_update_receipts WHERE bot_instance_id=$1",
                    instance,
                )
                await conn.execute(
                    "DELETE FROM omni_telegram_dialogues WHERE bot_instance_id=$1", instance
                )
            await store.close()

    asyncio.run(scenario())
