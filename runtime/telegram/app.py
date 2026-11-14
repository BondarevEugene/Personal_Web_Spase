"""OmniFactory Telegram runtime v1: webhook and bounded dialogue execution.

This runtime does NOT set Telegram's webhook automatically and does not
claim persistent state. Deploy with ONE replica until Redis-backed state
and deduplication are implemented.
"""
from __future__ import annotations

import base64
import json
import os
import re
import secrets
from contextlib import asynccontextmanager
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, Update)
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

TOKEN_PATTERN = re.compile(r"^[0-9]{5,15}:[A-Za-z0-9_-]{30,100}$")
from scenario import read_scenario
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


def build_runtime(scenario: dict, bot: Bot, webhook_secret: str) -> FastAPI:
    nodes = {node["id"]: node for node in scenario["nodes"]}
    dp = Dispatcher()
    router = Router()
    cursor: dict[tuple[int, int], str] = {}
    values: dict[tuple[int, int], dict[str, str]] = {}

    async def walk(chat_id: int, user_id: int, target: str) -> None:
        key = (chat_id, user_id)
        current = values.setdefault(key, {})
        for _ in range(50):
            node = nodes.get(target)
            if node is None:
                cursor.pop(key, None)
                values.pop(key, None)
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
                return
            target = node.get("next")
            if target is None:
                cursor.pop(key, None)
                values.pop(key, None)
                return
        cursor.pop(key, None)
        values.pop(key, None)
        await bot.send_message(chat_id, "Сценарий содержит слишком длинный цикл.")

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        if message.from_user:
            key = (message.chat.id, message.from_user.id)
            cursor.pop(key, None)
            values.pop(key, None)
            await walk(*key, scenario["start"])

    @router.callback_query(F.data.startswith("omni:"))
    async def choose(call: CallbackQuery) -> None:
        try:
            _, node_id, number = (call.data or "").split(":", 2)
            key = (call.message.chat.id, call.from_user.id)
            node = nodes[node_id]
            if (node["kind"] != "choice" or cursor.get(key) != node_id or
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
        target = cursor.get(key)
        node = nodes.get(target) if target else None
        if not node or node["kind"] != "input":
            await message.answer("Начни с /start.")
            return
        if not message.text or not message.text.strip() or len(message.text) > 300:
            await message.answer("Отправь текст до 300 символов.")
            return
        values.setdefault(key, {})[node["variable"]] = message.text.strip()
        await walk(*key, node["next"])

    dp.include_router(router)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            yield
        finally:
            await bot.session.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    async def health():
        # This proves the local runtime process is serving, NOT Telegram delivery.
        return {"service": "omni-telegram-runtime", "status": "process_ready",
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
        await dp.feed_update(bot, event)
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
    return build_runtime(scenario, Bot(token), webhook_secret)


app = load_app() if os.getenv("OMNI_RUNTIME_BOOT") == "1" else FastAPI(
    docs_url=None, redoc_url=None, openapi_url=None
)
