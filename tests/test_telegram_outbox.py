"""PostgreSQL outbox acceptance tests: atomic staging and ambiguous delivery."""
import asyncio
import os
import uuid

import pytest

from runtime.telegram.outbox import counters, dispatch_once
from runtime.telegram.state import Conversation, PostgresStateStore

DSN = os.getenv("OMNI_TEST_RUNTIME_POSTGRES_URL")


def run(task):
    return asyncio.run(task)


async def setup():
    return await PostgresStateStore.connect(
        DSN, "outbox_" + uuid.uuid4().hex, bootstrap_schema=True)


@pytest.mark.skipif(not DSN, reason="Requires disposable PostgreSQL CI service")
def test_atomic_commit_and_no_duplicate_send():
    async def check():
        store = await setup()
        try:
            async def stage(state: Conversation):
                state.cursor = "next"
                state.queue_message(101, "Hello user")
                state.queue_message(101, "Second message")
            assert (await store.process(101, 101, 20, stage))[0] == "processed"
            assert (await store.process(101, 101, 20, stage))[0] == "duplicate"
            assert (await counters(store)).get("pending") == 2
            sent = []
            async def sender(command):
                sent.append((command.seq, command.payload["text"]))
            assert await dispatch_once(store, sender) == "sent"
            assert await dispatch_once(store, sender) == "sent"
            assert await dispatch_once(store, sender) == "empty"
            assert sent == [(0, "Hello user"), (1, "Second message")]
            assert (await counters(store)).get("sent") == 2
            await store.close()
            again = await PostgresStateStore.connect(DSN, store.bot_instance_id)
            assert (await counters(again)).get("sent") == 2
            await again.close()
        finally:
            if not store.pool._closed:
                await store.close()
    run(check())


@pytest.mark.skipif(not DSN, reason="Requires disposable PostgreSQL CI service")
def test_unknown_send_never_automatically_retries():
    async def check():
        store = await setup()
        try:
            async def stage(state):
                state.queue_message(102, "Could have been sent")
            await store.process(105, 102, 22, stage)
            attempts = 0
            async def uncertain(command):
                nonlocal attempts
                attempts += 1
                raise OSError("Connection lost after possible remote send")
            assert await dispatch_once(store, uncertain) == "needs_reconciliation"
            assert await dispatch_once(store, uncertain) == "empty"
            assert attempts == 1
            assert (await counters(store)).get("needs_reconciliation") == 1
        finally:
            await store.close()
    run(check())


@pytest.mark.skipif(not DSN, reason="Requires disposable PostgreSQL CI service")
def test_two_workers_do_not_send_same_command():
    async def check():
        store = await setup()
        try:
            async def stage(state):
                state.queue_message(103, "Once")
            await store.process(106, 103, 23, stage)
            seen = 0
            async def sender(command):
                nonlocal seen
                seen += 1
                await asyncio.sleep(0.1)
            outcomes = await asyncio.gather(
                dispatch_once(store, sender), dispatch_once(store, sender))
            assert sorted(outcomes) == ["empty", "sent"]
            assert seen == 1
        finally:
            await store.close()
    run(check())


@pytest.mark.skipif(not DSN, reason="Requires disposable PostgreSQL CI service")
def test_staging_error_rolls_back_all_messages_and_dialogue():
    async def check():
        store = await setup()
        try:
            async def broken(state):
                state.queue_message(104, "Should not persist")
                state.cursor = "next"
                raise ValueError("scenario failed before commit")
            from runtime.telegram.state import AmbiguousDelivery
            with pytest.raises(AmbiguousDelivery):
                await store.process(107, 104, 24, broken)
            assert (await counters(store)).get("pending", 0) == 0
            assert await store.receipt_status(107) == "needs_reconciliation"
        finally:
            await store.close()
    run(check())


def test_unapproved_outbox_worker_fails_closed(monkeypatch):
    from runtime.telegram.outbox import serve_one
    monkeypatch.delenv("OMNI_OUTBOX_SEND_ENABLED", raising=False)
    with pytest.raises(RuntimeError, match="disabled"):
        run(serve_one())


def test_outgoing_payload_is_strictly_bounded():
    state = Conversation(cursor=None, values={})
    with pytest.raises(ValueError):
        state.queue_message(20, "")
    with pytest.raises(ValueError):
        state.queue_message(20, "x" * 4001)
    state.queue_message(20, "ok")
    assert state.outbox[0] == {"chat_id": 20, "method": "send_message", "text": "ok"}
