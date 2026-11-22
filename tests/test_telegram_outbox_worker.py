"""Outbox worker contract tests without external Telegram or PostgreSQL."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from runtime.telegram.outbox_worker import WorkerSettings, run_worker


def test_worker_drains_then_stops():
    async def scenario():
        stop = asyncio.Event()
        calls = []

        async def fake_dispatch(_store, _sender):
            calls.append("dispatch")
            if len(calls) == 2:
                stop.set()
            return "sent"

        with patch("runtime.telegram.outbox_worker.dispatch_once", fake_dispatch):
            await asyncio.wait_for(
                run_worker(SimpleNamespace(), AsyncMock(), stop), timeout=1
            )
        assert calls == ["dispatch", "dispatch"]

    asyncio.run(scenario())


def test_worker_halts_on_ambiguous_delivery():
    async def scenario():
        with patch("runtime.telegram.outbox_worker.dispatch_once", AsyncMock(
            return_value="needs_reconciliation"
        )) as dispatch:
            await asyncio.wait_for(
                run_worker(SimpleNamespace(), AsyncMock(), asyncio.Event()), timeout=1
            )
        dispatch.assert_awaited_once()

    asyncio.run(scenario())


def test_worker_idle_exits_on_shutdown():
    async def scenario():
        stop = asyncio.Event()

        async def fake_dispatch(_store, _sender):
            stop.set()
            return "empty"

        with patch("runtime.telegram.outbox_worker.dispatch_once", fake_dispatch):
            await asyncio.wait_for(
                run_worker(SimpleNamespace(), AsyncMock(), stop), timeout=1
            )

    asyncio.run(scenario())


def test_worker_recovers_from_transient_database_error():
    async def scenario():
        stop = asyncio.Event()
        attempts = 0

        async def fake_dispatch(_store, _sender):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise OSError("temporary")
            stop.set()
            return "sent"

        with patch("runtime.telegram.outbox_worker.dispatch_once", fake_dispatch):
            await asyncio.wait_for(
                run_worker(
                    SimpleNamespace(), AsyncMock(), stop,
                    WorkerSettings(poll_seconds=0.1, error_seconds=0.1),
                ), timeout=2
            )
        assert attempts == 2

    asyncio.run(scenario())


def test_rejects_invalid_poll_intervals():
    import pytest

    with pytest.raises(ValueError):
        WorkerSettings(poll_seconds=0)
    with pytest.raises(ValueError):
        WorkerSettings(error_seconds=301)
