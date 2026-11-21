"""OmniFactory Telegram runtime v1: webhook and bounded dialogue execution.

This runtime does NOT set Telegram's webhook automatically and does not
claim persistent state. Deploy with ONE replica until Redis-backed state
and deduplication are implemented.
"""
from __future__ import annotations

import os
import re
import secrets
from contextlib import asynccontextmanager
from contextvars import ContextVar

from state import AmbiguousDelivery, Conversation, PostgresStateStore
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, Update)
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

TOKEN_PATTERN = re.compile(r"^[0-9]{5,15}:[A-Za-z0-9_-]{30,100}$")
from scenario import BODY_LIMIT, read_scenario
PLACEHOLDER = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]{0,39})\}\}")

def substitute(value: str, variables: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda match: variables.get(match.group(1), ""), value)


def matches(actual: str, operator: str, expected: str) -> bool:
    return {
        "equals": lambda: actual == expected,
        "not_equals": lambda: actual != expected,
        "contains": lambda: expected in actual,
        "not_empty": lambda: bool(actual.strip()),
    }[operator]()


def build_runtime(scenario: dict, bot: Bot, webhook_secret: str, *,
                  require_state: bool = False) -> FastAPI:
    nodes = {node["id"]: node for node in scenario["nodes"]}
    dp = Dispatcher()
    router = Router()
    # ContextVars isolate each Telegram update; only dev/test mode uses RAM.
    local_cursor: dict[tuple[int, int], str] = {}
    local_values: dict[tuple[int, int], dict[str, str]] = {}
    cursor_ctx: ContextVar[dict] = ContextVar("cursor")
    values_ctx: ContextVar[dict] = ContextVar("values")
    storage: dict[str, PostgresStateStore | None] = {"store": None}

    async def walk(chat_id: int, user_id: int, target: str) -> None:
        key = (chat_id, user_id)
        current = values_ctx.get().setdefault(key, {})
        for _ in range(50):
            node = nodes.get(target)
            if node is None:
                cursor_ctx.get().pop(key, None)
                values_ctx.get().pop(key, None)
                return
            kind = node["kind"]
            text = substitute(node.get("text") or "", current)
            if kind == "condition":
                actual = current.get(node["variable"], "")
                expected = substitute(node.get("value") or "", current)
                target = node["true_target"] if matches(actual, node["operator"], expected) else node["false_target"]
                continue
            if kind == "set_variable":
                current[node["variable"]] = substitute(node.get("value") or "", current)[:300]
                target = node["next"]
                continue
            if kind in {"choice", "input"}:
                cursor_ctx.get()[key] = target
                if kind == "input":
                    await bot.send_message(chat_id, text)
                else:
                    keys = [[InlineKeyboardButton(
                        text=option["label"], callback_data="omni:"+target+":"+str(i))]
                        for i, option in enumerate(node["options"])]
                    await bot.send_message(chat_id, text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keys))
                return
            if kind == "message":
                if text:
                    await bot.send_message(chat_id, text)
            elif kind == "photo":
                await bot.send_photo(chat_id, photo=node["media"], caption=text or None)
            elif kind == "document":
                await bot.send_document(chat_id, document=node["media"], caption=text or None)
            elif kind == "end":
                if text:
                    await bot.send_message(chat_id, text)
                cursor_ctx.get().pop(key, None)
                values_ctx.get().pop(key, None)
                return
            target = node.get("next")
            if target is None:
                cursor_ctx.get().pop(key, None)
                values_ctx.get().pop(key, None)
                return
        cursor_ctx.get().pop(key, None)
        values_ctx.get().pop(key, None)
        await bot.send_message(chat_id, "Сценарий содержит слишком длинный цикл.")

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        if message.from_user:
            key = (message.chat.id, message.from_user.id)
            cursor_ctx.get().pop(key, None)
            values_ctx.get().pop(key, None)
            await walk(*key, scenario["start"])

    @router.callback_query(F.data.startswith("omni:"))
    async def choose(call: CallbackQuery) -> None:
        try:
            _, node_id, number = (call.data or "").split(":", 2)
            key = (call.message.chat.id, call.from_user.id)
            node = nodes[node_id]
            if (node["kind"] != "choice" or cursor_ctx.get().get(key) != node_id or
                    not number.isascii() or not number.isdecimal()):
                raise ValueError
            index = int(number)
            target = node["options"][index]["target"]
        except (AttributeError, TypeError, ValueError, KeyError, IndexError):
            await call.answer("Выбор устарел. Используй /start.", show_alert=True)
            return
        await call.answer()
        await walk(*key, target)

    @router.message()
    async def text_input(message: Message) -> None:
        if message.from_user is None:
            return
        key = (message.chat.id, message.from_user.id)
        target = cursor_ctx.get().get(key)
        node = nodes.get(target) if target else None
        if not node or node["kind"] != "input":
            await message.answer("Начни с /start.")
            return
        if not message.text or not message.text.strip() or len(message.text) > 300:
            await message.answer("Отправь текст до 300 символов.")
            return
        values_ctx.get().setdefault(key, {})[node["variable"]] = message.text.strip()
        await walk(*key, node["next"])

    dp.include_router(router)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            if require_state:
                storage["store"] = await PostgresStateStore.connect(
                    os.getenv("OMNI_RUNTIME_DATABASE_URL", ""),
                    os.getenv("OMNI_BOT_INSTANCE_ID", ""),
                    bootstrap_schema=os.getenv("OMNI_RUNTIME_BOOTSTRAP_SCHEMA") == "1",
                )
            yield
        finally:
            if storage["store"] is not None:
                await storage["store"].close()
            await bot.session.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    async def health():
        # DB health is checked; Telegram delivery still needs an E2E probe.
        if require_state:
            active = storage["store"]
            if active is None:
                raise HTTPException(503, "Runtime state unavailable")
            try:
                async with active.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
            except Exception:
                raise HTTPException(503, "Runtime state unavailable")
        return {"service": "omni-telegram-runtime", "status": "process_ready",
                "state": "postgresql" if require_state else "volatile_test_only",
                "telegram_delivery_verified": False}

    @app.get("/internal/state")
    async def internal_state(request: Request):
        # Private operator metrics only; never return chat IDs or conversations.
        expected = os.getenv("OMNI_RUNTIME_OBSERVABILITY_TOKEN", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", expected):
            raise HTTPException(404, "Not found")
        supplied = request.headers.get("X-Omni-Operator-Token", "")
        if not secrets.compare_digest(expected, supplied):
            raise HTTPException(403, "Forbidden")
        store = storage["store"]
        if store is None:
            raise HTTPException(503, "Durable storage not active")
        try:
            counts = await store.counts()
        except Exception:
            raise HTTPException(503, "Runtime counters unavailable")
        return {"service": "omni-telegram-runtime", "storage": "postgresql",
                "processed": counts.get("processed", 0),
                "in_progress": counts.get("processing", 0),
                "needs_reconciliation": counts.get("needs_reconciliation", 0),
                "telegram_delivery_verified": False}

    @app.post("/telegram/webhook")
    async def webhook(request: Request):
        supplied = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secrets.compare_digest(supplied, webhook_secret):
            raise HTTPException(403, "Invalid Telegram webhook signature")
        if request.headers.get("content-length", "").isdigit() and int(
                request.headers["content-length"]) > BODY_LIMIT:
            raise HTTPException(413, "Update too large")
        payload = await request.body()
        if len(payload) > BODY_LIMIT:
            raise HTTPException(413, "Update too large")
        try:
            event = Update.model_validate_json(payload, context={"bot": bot})
        except (ValueError, TypeError):
            raise HTTPException(400, "Invalid Telegram update")
        # Scope dialogue state to one inbound Telegram update.
        message = event.message
        query = event.callback_query
        if query is not None:
            message = query.message
        sender = query.from_user if query is not None else (
            message.from_user if message is not None else None)
        chat = getattr(message, "chat", None)
        chat_id = chat.id if chat is not None else 0
        user_id = sender.id if sender is not None else 0
        key = (chat_id, user_id)

        async def handle(state: Conversation):
            cursors = {key: state.cursor} if state.cursor else {}
            variables = {key: dict(state.values)}
            ctoken = cursor_ctx.set(cursors)
            vtoken = values_ctx.set(variables)
            try:
                await dp.feed_update(bot, event)
                state.cursor = cursors.get(key)
                state.values = variables.get(key, {})
            finally:
                cursor_ctx.reset(ctoken)
                values_ctx.reset(vtoken)

        store = storage["store"]
        if store is None:
            if require_state:
                raise HTTPException(503, "Runtime storage not ready")
            # Test/development only: volatile dialogue semantics.
            state = Conversation(local_cursor.get(key), local_values.get(key, {}))
            await handle(state)
            if state.cursor is None:
                local_cursor.pop(key, None)
            else:
                local_cursor[key] = state.cursor
            local_values[key] = state.values
            return JSONResponse({"ok": True, "state": "volatile"})
        try:
            status, _ = await store.process(event.update_id, chat_id, user_id, handle)
        except AmbiguousDelivery:
            raise HTTPException(503, "Update quarantined for operator reconciliation")
        return JSONResponse({"ok": True, "receipt": status})

    return app


def load_app() -> FastAPI:
    token = os.getenv("BOT_TOKEN", "")
    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    encoded = os.getenv("OMNI_SCENARIO_BASE64", "")
    if not TOKEN_PATTERN.fullmatch(token):
        raise RuntimeError("Missing or invalid BOT_TOKEN")
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", webhook_secret):
        raise RuntimeError("Missing or invalid TELEGRAM_WEBHOOK_SECRET")
    try:
        scenario = read_scenario(encoded)
    except ValueError as exc:
        raise RuntimeError("Invalid runtime scenario") from exc
    return build_runtime(scenario, Bot(token), webhook_secret, require_state=True)


app = load_app() if os.getenv("OMNI_RUNTIME_BOOT") == "1" else FastAPI(
    docs_url=None, redoc_url=None, openapi_url=None
)
