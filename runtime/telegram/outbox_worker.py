"""Conservative continuous Telegram outbox worker.

A claimed command is never automatically replayed after a crash or network
error: the Telegram API has no idempotency key for sendMessage. Operators
must reconcile ambiguous outcomes before manually changing any status.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
from contextlib import suppress
from dataclasses import dataclass
from typing import Awaitable, Callable

from aiogram import Bot

try:
    from runtime.telegram.outbox import Command, counters, dispatch_once
    from runtime.telegram.postgres_state import PostgresStateStore
except ModuleNotFoundError:
    from outbox import Command, counters, dispatch_once
    from postgres_state import PostgresStateStore

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkerSettings:
    poll_seconds: float = 1.0
    error_seconds: float = 5.0

    def __post_init__(self) -> None:
        if not 0.1 <= self.poll_seconds <= 60 or not 0.1 <= self.error_seconds <= 300:
            raise ValueError("Invalid worker polling interval")


async def run_worker(
    store: PostgresStateStore,
    sender: Callable[[Command], Awaitable[None]],
    stop: asyncio.Event,
    settings: WorkerSettings = WorkerSettings(),
) -> None:
    """Dispatch sequentially; halt on an ambiguous send rather than skip it."""
    while not stop.is_set():
        try:
            result = await dispatch_once(store, sender)
            if result == "needs_reconciliation":
                LOG.error("Outbox delivery ambiguous; worker stopped for reconciliation")
                return
            if result == "sent":
                continue
            # An empty queue is normal. A timed wait allows prompt shutdown.
            with suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=settings.poll_seconds)
        except (OSError, ConnectionError, TimeoutError):
            LOG.exception("Outbox database temporarily unavailable")
            with suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=settings.error_seconds)


async def run_service(settings: WorkerSettings) -> None:
    if os.getenv("OMNI_OUTBOX_SEND_ENABLED") != "1":
        raise RuntimeError("Outbound delivery requires explicit OMNI_OUTBOX_SEND_ENABLED=1")
    from aiogram import Bot
    try:
        from runtime.telegram.app import TOKEN_PATTERN
    except ModuleNotFoundError:
        from app import TOKEN_PATTERN

    token = os.getenv("BOT_TOKEN", "")
    if not TOKEN_PATTERN.fullmatch(token):
        raise RuntimeError("Missing or invalid BOT_TOKEN")
    dsn = os.getenv("OMNI_RUNTIME_DATABASE_URL", "")
    instance = os.getenv("OMNI_BOT_INSTANCE_ID", "")
    store = await PostgresStateStore.connect(dsn, instance)
    bot = Bot(token)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in ("SIGTERM", "SIGINT"):
        sig = getattr(signal, name, None)
        if sig is not None:
            with suppress(NotImplementedError, RuntimeError):
                loop.add_signal_handler(sig, stop.set)

    async def send(item: Command) -> None:
        await bot.send_message(item.chat_id, item.payload["text"])

    try:
        counts = await counters(store)
        LOG.info("Outbox starting: pending=%s claimed=%s ambiguous=%s",
                 counts.get("pending", 0), counts.get("claimed", 0),
                 counts.get("needs_reconciliation", 0))
        if counts.get("claimed", 0) or counts.get("needs_reconciliation", 0):
            raise RuntimeError("Unreconciled outbox items; resolve before starting sender")
        await run_worker(store, send, stop, settings)
    finally:
        await bot.session.close()
        await store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Conservative Telegram outbox worker")
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--error-seconds", type=float, default=5.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_service(WorkerSettings(args.poll_seconds, args.error_seconds)))


if __name__ == "__main__":
    main()
