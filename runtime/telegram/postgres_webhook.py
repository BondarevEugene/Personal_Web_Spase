"""PostgreSQL transactional Telegram webhook: commit dialogue and outbox together.

This mode intentionally supports text/choice/input/conditions only. Media nodes
fail closed until media commands have their own transactional sender contract.
"""
from __future__ import annotations

import os
import re
import secrets
from contextlib import asynccontextmanager

from aiogram import Bot
from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from runtime.telegram.postgres_state import AmbiguousDelivery, Conversation, PostgresStateStore
from runtime.telegram.scenario import BODY_LIMIT

PLACEHOLDER = re.compile(r"\\{\\{([A-Za-z][A-Za-z0-9_-]{0,39})\\}\\}")


def render(text: str, values: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda m: values.get(m.group(1), ""), text)


def advance(spec: dict, state: Conversation, chat_id: int, target: str) -> None:
    nodes = {node["id"]: node for node in spec["nodes"]}
    for _ in range(50):
        node = nodes[target]
        kind = node["kind"]
        text = render(node.get("text") or "", state.values)
        if kind == "condition":
            actual = state.values.get(node["variable"], "")
            expected = render(node.get("value") or "", state.values)
            op = node["operator"]
            matched = (actual == expected if op == "equals" else
                       actual != expected if op == "not_equals" else
                       expected in actual if op == "contains" else bool(actual.strip()))
            target = node["true_target"] if matched else node["false_target"]
            continue
        if kind == "set_variable":
            state.values[node["variable"]] = render(node.get("value") or "", state.values)[:300]
            target = node["next"]
            continue
        if kind in {"photo", "document"}:
            raise ValueError("PostgreSQL runtime does not support media delivery yet")
        if kind == "choice":
            # Explicit text-only options until transactional inline keyboards are supported.
            options = "\\n".join(f"{i + 1}. {opt['label']}" for i, opt in enumerate(node["options"]))
            state.queue_message(chat_id, f"{text}\\n{options}".strip())
            state.cursor = target
            return
        if kind == "input":
            state.queue_message(chat_id, text)
            state.cursor = target
            return
        if text:
            state.queue_message(chat_id, text)
        if kind == "end":
            state.cursor = None
            state.values.clear()
            return
        target = node["next"]
    raise ValueError("Scenario step budget exceeded")


def apply_update(spec: dict, state: Conversation, event: Update) -> None:
    message = event.message
    callback = event.callback_query
    if callback is not None:
        raise ValueError("Callback delivery unsupported in PostgreSQL text mode")
    if message is None or message.from_user is None:
        return
    text = message.text or ""
    if text.startswith("/start"):
        state.values.clear()
        state.cursor = None
        advance(spec, state, message.chat.id, spec["start"])
        return
    nodes = {node["id"]: node for node in spec["nodes"]}
    node = nodes.get(state.cursor) if state.cursor else None
    if node and node["kind"] == "input":
        if not text.strip() or len(text) > 300:
            state.queue_message(message.chat.id, "Отправь текст до 300 символов.")
            return
        state.values[node["variable"]] = text.strip()
        advance(spec, state, message.chat.id, node["next"])
    elif node and node["kind"] == "choice":
        if not text.isascii() or not text.isdecimal():
            state.queue_message(message.chat.id, "Выбери номер варианта.")
            return
        index = int(text) - 1
        if index < 0 or index >= len(node["options"]):
            state.queue_message(message.chat.id, "Выбери номер варианта.")
            return
        advance(spec, state, message.chat.id, node["options"][index]["target"])
    else:
        state.queue_message(message.chat.id, "Начни с /start.")


def build_postgres_runtime(spec: dict, bot: Bot, secret: str, store: PostgresStateStore) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            await bot.session.close()
            await store.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    async def health():
        return {"service": "omni-telegram-runtime", "status": "process_ready",
                "telegram_delivery_verified": False, "storage": "postgresql"}

    @app.get("/ready")
    async def ready():
        try:
            async with store.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return {"ready": True, "mode": "postgresql",
                    "telegram_delivery_verified": False}
        except Exception:
            return JSONResponse({"ready": False, "mode": "postgresql"}, status_code=503)

    @app.get("/outbox/health")
    async def outbox_health():
        from runtime.telegram.outbox import counters
        try:
            return {"outbox": await counters(store), "delivery_verified": False}
        except Exception:
            return JSONResponse({"ready": False}, status_code=503)

    @app.post("/telegram/webhook")
    async def webhook(request: Request):
        supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secrets.compare_digest(supplied, secret):
            raise HTTPException(403, "Invalid Telegram webhook signature")
        if request.headers.get("content-length", "").isdigit() and int(
                request.headers["content-length"]) > BODY_LIMIT:
            raise HTTPException(413, "Update too large")
        payload = await request.body()
        if len(payload) > BODY_LIMIT:
            raise HTTPException(413, "Update too large")
        try:
            event = Update.model_validate_json(payload, context={"bot": bot})
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, "Invalid Telegram update") from exc
        message = event.message
        if message is None or message.from_user is None:
            raise HTTPException(422, "Only message updates are supported in PostgreSQL mode")
        async def execute(state: Conversation):
            apply_update(spec, state, event)
        try:
            status, _ = await store.process(
                event.update_id, message.chat.id, message.from_user.id, execute)
        except AmbiguousDelivery as exc:
            raise HTTPException(503, "Update requires operator reconciliation") from exc
        return {"ok": True, "duplicate": status == "duplicate", "queued": status == "processed"}

    return app


async def load_postgres_app(spec: dict, bot: Bot, secret: str) -> FastAPI:
    store = await PostgresStateStore.connect(
        os.getenv("OMNI_RUNTIME_DATABASE_URL", ""),
        os.getenv("OMNI_BOT_INSTANCE_ID", ""))
    return build_postgres_runtime(spec, bot, secret, store)
