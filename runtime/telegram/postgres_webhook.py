"""PostgreSQL webhook: atomic dialogue, media, callback and outbound actions."""
from __future__ import annotations

import os
import re
import secrets
from contextlib import asynccontextmanager

import asyncpg
from aiogram import Bot
from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

try:
    from runtime.telegram.postgres_state import (
        AmbiguousDelivery,
        Conversation,
        PostgresStateStore,
    )
    from runtime.telegram.scenario import BODY_LIMIT
except ModuleNotFoundError:
    from postgres_state import AmbiguousDelivery, Conversation, PostgresStateStore
    from scenario import BODY_LIMIT

PLACEHOLDER = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]{0,39})\}\}")


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
            media = node.get("media")
            if not isinstance(media, str) or not media or len(media) > 2048:
                raise ValueError("Invalid media reference")
            payload = {kind: media}
            if text:
                if len(text) > 1024:
                    raise ValueError("Media caption too long")
                payload["caption"] = text
            state.queue_action(chat_id, "send_" + kind, payload)
            target = node["next"]
            continue
        if kind == "choice":
            options = "\n".join(f"{i + 1}. {opt['label']}" for i, opt in enumerate(node["options"]))
            buttons = [[{"text": opt["label"], "callback_data": f"omni:{target}:{i}"}]
                       for i, opt in enumerate(node["options"])]
            state.queue_message(chat_id, f"{text}\n{options}".strip(),
                                {"inline_keyboard": buttons})
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
        data = callback.data or ""
        chat_id = callback.message.chat.id
        nodes = {node["id"]: node for node in spec["nodes"]}
        node = nodes.get(state.cursor) if state.cursor else None
        parts = data.split(":")
        valid = (len(parts) == 3 and parts[0] == "omni"
                 and node is not None and node["kind"] == "choice"
                 and parts[1] == state.cursor and parts[2].isascii()
                 and parts[2].isdecimal())
        index = int(parts[2]) if valid else -1
        if not valid or not 0 <= index < len(node["options"]):
            state.queue_action(chat_id, "answer_callback_query",
                               {"callback_query_id": callback.id,
                                "text": "Выбор устарел. Используй /start.",
                                "show_alert": True})
            return
        state.queue_action(chat_id, "answer_callback_query",
                           {"callback_query_id": callback.id})
        advance(spec, state, chat_id, node["options"][index]["target"])
        return
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


def build_postgres_runtime(spec: dict, bot: Bot, secret: str, store: PostgresStateStore | None = None) -> FastAPI:
    holder: dict[str, PostgresStateStore] = {}

    def active_store() -> PostgresStateStore:
        return holder["store"]
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        holder["store"] = store or await PostgresStateStore.connect(
            os.getenv("OMNI_RUNTIME_DATABASE_URL", ""),
            os.getenv("OMNI_BOT_INSTANCE_ID", ""))
        try:
            yield
        finally:
            await bot.session.close()
            await active_store().close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    async def health():
        return {"service": "omni-telegram-runtime", "status": "process_ready",
                "telegram_delivery_verified": False, "storage": "postgresql"}

    @app.get("/ready")
    async def ready():
        try:
            async with active_store().pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return {"ready": True, "mode": "postgresql",
                    "telegram_delivery_verified": False}
        except (asyncpg.PostgresError, OSError, TimeoutError):
            return JSONResponse({"ready": False, "mode": "postgresql"}, status_code=503)

    @app.get("/outbox/health")
    async def outbox_health():
        try:
            from runtime.telegram.outbox import counters
        except ModuleNotFoundError:
            from outbox import counters
        try:
            return {"outbox": await counters(active_store()), "delivery_verified": False}
        except (asyncpg.PostgresError, OSError, TimeoutError):
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
        callback = event.callback_query
        if message is not None and message.from_user is not None:
            chat_id, user_id = message.chat.id, message.from_user.id
        elif callback is not None and callback.message is not None:
            chat_id, user_id = callback.message.chat.id, callback.from_user.id
        else:
            raise HTTPException(422, "Unsupported Telegram update")
        async def execute(state: Conversation):
            apply_update(spec, state, event)
        try:
            status, _ = await active_store().process(
                event.update_id, chat_id, user_id, execute)
        except AmbiguousDelivery as exc:
            raise HTTPException(503, "Update requires operator reconciliation") from exc
        return {"ok": True, "duplicate": status == "duplicate", "queued": status == "processed"}

    return app


async def load_postgres_app(spec: dict, bot: Bot, secret: str) -> FastAPI:
    store = await PostgresStateStore.connect(
        os.getenv("OMNI_RUNTIME_DATABASE_URL", ""),
        os.getenv("OMNI_BOT_INSTANCE_ID", ""))
    return build_postgres_runtime(spec, bot, secret, store)
