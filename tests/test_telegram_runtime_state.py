"""Real PostgreSQL runtime acceptance: persistence, isolation, replay and quarantine.

Requires OMNI_TEST_RUNTIME_POSTGRES_URL pointing at a throwaway DB. Otherwise
tests skip rather than connecting to application production credentials.
"""
import asyncio
import os
import uuid

import pytest

from runtime.telegram.state import AmbiguousDelivery, Conversation, PostgresStateStore

DB = os.getenv("OMNI_TEST_RUNTIME_POSTGRES_URL")


def execute(coro):
    return asyncio.run(coro)


async def instance() -> PostgresStateStore:
    assert DB
    name = "test_" + uuid.uuid4().hex
    return await PostgresStateStore.connect(DB, name, bootstrap_schema=True)


@pytest.mark.skipif(not DB, reason="Requires disposable runtime Postgres")
def test_persistent_state_after_close_and_reopen():
    async def run():
        store = await instance()
        async def first(state: Conversation):
            state.cursor = "ask_name"
            state.values["name"] = "Alice"
            return "sent"
        status, result = await store.process(5, 42, 17, first)
        assert (status, result) == ("processed", "sent")
        await store.close()
        again = await PostgresStateStore.connect(DB, store.bot_instance_id)
        assert await again.receipt_status(5) == "processed"
        assert await again.process(5, 42, 17, first) == ("duplicate", None)
        async def second(state: Conversation):
            assert state.cursor == "ask_name"
            assert state.values == {"name": "Alice"}
            state.cursor = None
        assert (await again.process(6, 42, 17, second))[0] == "processed"
        await again.close()
    execute(run())


@pytest.mark.skipif(not DB, reason="Requires disposable runtime Postgres")
def test_quarantine_failed_send_prevents_blind_replay():
    async def run():
        store = await instance()
        calls = 0
        async def send(state):
            nonlocal calls
            calls += 1
            state.cursor = "sent"
            raise OSError("Unknown send outcome")
        with pytest.raises(AmbiguousDelivery):
            await store.process(100, 55, 33, send)
        assert await store.receipt_status(100) == "needs_reconciliation"
        with pytest.raises(AmbiguousDelivery):
            await store.process(100, 55, 33, send)
        assert calls == 1
        assert (await store.counts())["needs_reconciliation"] == 1
        await store.close()
    execute(run())


@pytest.mark.skipif(not DB, reason="Requires disposable runtime Postgres")
def test_exact_update_id_concurrency_and_bot_namespace_isolation():
    async def run():
        store = await instance()
        other = await PostgresStateStore.connect(DB, "different_" + uuid.uuid4().hex)
        seen = 0
        async def send(state):
            nonlocal seen
            seen += 1
            await asyncio.sleep(0.06)
            state.values["counter"] = str(int(state.values.get("counter", "0")) + 1)
        first = asyncio.create_task(store.process(200, 123, 456, send))
        await asyncio.sleep(.02)
        # Depending on scheduling, the retry sees either processing
        # (quarantine) or already processed (duplicate). It must never send.
        try:
            retry_status, _ = await store.process(200, 123, 456, send)
        except AmbiguousDelivery:
            pass
        else:
            assert retry_status == "duplicate"
        assert (await first)[0] == "processed"
        assert seen == 1
        assert (await other.process(200, 123, 456, send))[0] == "processed"
        assert seen == 2
        assert await store.receipt_status(200) == "processed"
        await store.close()
        await other.close()
    execute(run())


@pytest.mark.skipif(not DB, reason="Requires disposable runtime Postgres")
def test_dialogue_scope_excludes_other_users():
    async def run():
        store = await instance()
        async def alice(state):
            assert state.cursor is None
            state.cursor = "alice_node"
            state.values["name"] = "Private"
        await store.process(301, 123, 1, alice)
        async def bob(state):
            assert state.cursor is None
            assert state.values == {}
        await store.process(302, 123, 2, bob)
        await store.close()
    execute(run())


def test_bad_bot_identity_fails_closed():
    with pytest.raises(ValueError):
        PostgresStateStore(None, "../../other_bot")


def test_production_state_not_silently_optional(monkeypatch):
    from runtime.telegram.state import StoreUnavailable
    async def run():
        with pytest.raises(StoreUnavailable):
            await PostgresStateStore.connect("", "valid_bot_name_123")
    execute(run())
