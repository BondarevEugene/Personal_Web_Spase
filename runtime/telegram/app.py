"""OmniFactory Telegram runtime v1: webhook and bounded dialogue execution.

This runtime does NOT set Telegram's webhook automatically. Deploy with ONE
replica and a persistent SQLite volume; multi-replica execution is unsupported.
"""
from __future__ import annotations

import asyncio
import os
import re
import secrets
import sqlite3
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from scenario import BODY_LIMIT, read_scenario
from state import DialogueStore

TOKEN_PATTERN = re.compile(r"^[0-9]{5,15}:[A-Za-z0-9_-]{30,100}$")
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


def build_runtime(scenario: dict, bot: Bot, webhook_secret: str,
                  store: DialogueStore | None = None) -> FastAPI:
    nodes = {node["id"]: node for node in scenario["nodes"]}
    dp = Dispatcher()
    router = Router()
    cursor: dict[tuple[int, int], str] = {}
    values: dict[tuple[int, int], dict[str, str]] = {}
    conversation_locks: dict[tuple[int, int], asyncio.Lock] = {}

    def load(key: tuple[int, int]) -> None:
        if store is not None:
            current_cursor, current_values = store.read(key)
            if current_cursor is not None:
                cursor[key] = current_cursor
            else:
                cursor.pop(key, None)
            values[key] = current_values

    def persist(key: tuple[int, int]) -> None:
        if store is not None:
            if key in cursor:
                store.write(key, cursor[key], values.get(key, {}))
            else:
                store.clear(key)

    async def walk(chat_id: int, user_id: int, target: str) -> None:
        key = (chat_id, user_id)
        current = values.setdefault(key, {})
        for _ in range(50):
            node = nodes.get(target)
            if node is None:
                cursor.pop(key, None)
                values.pop(key, None)
                persist(key)
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
                cursor[key] = target
                if kind == "input":
                    await bot.send_message(chat_id, text)
                else:
                    keys = [[InlineKeyboardButton(
                        text=option["label"], callback_data="omni:"+target+":"+str(i))]
                        for i, option in enumerate(node["options"])]
                    await bot.send_message(chat_id, text,
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=keys))
                persist(key)
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
                cursor.pop(key, None)
                values.pop(key, None)
                persist(key)
                return
            target = node.get("next")
            if target is None:
                cursor.pop(key, None)
                values.pop(key, None)
                persist(key)
                return
        cursor.pop(key, None)
        values.pop(key, None)
        persist(key)
        await bot.send_message(chat_id, "Сценарий содержит слишком длинный цикл.")

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        if message.from_user:
            key = (message.chat.id, message.from_user.id)
            cursor.pop(key, None)
            values.pop(key, None)
            persist(key)
            await walk(*key, scenario["start"])

    @router.callback_query(F.data.startswith("omni:"))
    async def choose(call: CallbackQuery) -> None:
        try:
            _, node_id, number = (call.data or "").split(":", 2)
            key = (call.message.chat.id, call.from_user.id)
            load(key)
            node = nodes[node_id]
            if (node["kind"] != "choice" or cursor.get(key) != node_id or
                    not number.isascii() or not number.isdecimal()):
                raise ValueError
            index = int(number)
            target = node["options"][index]["target"]
        except (AttributeError, TypeError, ValueError, KeyError, IndexError):
            await call.answer("Выбор устарел. Используй /start.", show_alert=True)
            return
        cursor.pop(key, None)
        persist(key)
        await call.answer()
        await walk(*key, target)

    @router.message()
    async def text_input(message: Message) -> None:
        if message.from_user is None:
            return
        key = (message.chat.id, message.from_user.id)
        load(key)
        target = cursor.get(key)
        node = nodes.get(target) if target else None
        if not node or node["kind"] != "input":
            await message.answer("Начни с /start.")
            return
        if not message.text or not message.text.strip() or len(message.text) > 300:
            await message.answer("Отправь текст до 300 символов.")
            return
        values.setdefault(key, {})[node["variable"]] = message.text.strip()
        cursor.pop(key, None)
        persist(key)
        await walk(*key, node["next"])

    dp.include_router(router)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            await bot.session.close()
            if store is not None:
                store.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    async def health():
        # This proves the local runtime process is serving, NOT Telegram delivery.
        return {"service": "omni-telegram-runtime", "status": "process_ready",
                "telegram_delivery_verified": False,
                "persistent_state": store is not None}

    @app.get("/ready")
    async def ready():
        """Local storage readiness; no secrets or conversation content."""
        if store is None:
            return JSONResponse({"ready": True, "mode": "volatile",
                                 "telegram_delivery_verified": False})
        try:
            healthy = store.check()
        except (sqlite3.Error, OSError, ValueError):
            healthy = False
        return JSONResponse(
            {"ready": healthy, "mode": "persistent",
             "telegram_delivery_verified": False},
            status_code=200 if healthy else 503,
        )

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
        if store is not None and not store.claim_update(event.update_id):
            return JSONResponse({"ok": True, "duplicate": True})
        # Serialize updates for one conversation to avoid lost cursor/variable writes.
        # Single-replica only: multiple replicas need a shared distributed lock.
        if event.message is not None and event.message.from_user is not None:
            key = (event.message.chat.id, event.message.from_user.id)
        elif (event.callback_query is not None
              and event.callback_query.message is not None):
            key = (event.callback_query.message.chat.id,
                   event.callback_query.from_user.id)
        else:
            key = None
        try:
            if key is None:
                await dp.feed_update(bot, event)
            else:
                lock = conversation_locks.setdefault(key, asyncio.Lock())
                async with lock:
                    await dp.feed_update(bot, event)
        except Exception:
            if store is not None:
                store.forget_update(event.update_id)
            raise
        if store is not None:
            store.complete_update(event.update_id)
        return JSONResponse({"ok": True})

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
    state_path = os.getenv("OMNI_STATE_SQLITE_PATH", "").strip()
    if os.getenv("OMNI_RUNTIME_PRODUCTION") == "1":
        if not state_path or not os.path.isabs(state_path):
            raise RuntimeError("Production requires absolute persistent SQLite path")
        if os.getenv("WEB_CONCURRENCY", "1") != "1":
            raise RuntimeError("Production requires a single worker")
    store = DialogueStore(state_path) if state_path else None
    return build_runtime(scenario, Bot(token), webhook_secret, store)


app = load_app() if os.getenv("OMNI_RUNTIME_BOOT") == "1" else FastAPI(
    docs_url=None, redoc_url=None, openapi_url=None
)
