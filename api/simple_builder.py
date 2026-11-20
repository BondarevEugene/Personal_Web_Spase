"""Safe, bounded export of elementary Telegram scenario graphs to runnable Python.

This module intentionally does NOT run Docker, execute customer code, store bot
tokens, persist projects on the server, or give access to OmniFactory CRM.
"""
from __future__ import annotations

import io
import json
import re
import zipfile
from collections import deque
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

router = APIRouter(prefix="/api/v1/builder/simple", tags=["Simple Telegram Builder"])

NODE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
FILE_ID = re.compile(r"^[A-Za-z0-9_:/=-]{10,300}$")


class ButtonChoice(BaseModel):
    label: str = Field(min_length=1, max_length=64)
    target: str = Field(min_length=1, max_length=40)


class ScenarioNode(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    kind: Literal["message", "choice", "photo", "document", "end", "input", "condition", "set_variable"]
    text: str = Field(default="", max_length=1500)
    next: str | None = Field(default=None, max_length=40)
    media: str | None = Field(default=None, max_length=300)
    options: list[ButtonChoice] = Field(default_factory=list, max_length=8)
    variable: str | None = Field(default=None, max_length=40)
    value: str = Field(default="", max_length=300)
    operator: Literal["equals", "not_equals", "contains", "not_empty"] = "equals"
    true_target: str | None = Field(default=None, max_length=40)
    false_target: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def validate_content(self):
        if not NODE_ID.fullmatch(self.id):
            raise ValueError("ID блока должен начинаться с латинской буквы и содержать только буквы, цифры, - или _")
        if self.kind in {"message", "choice", "input"} and not self.text.strip():
            raise ValueError("Текст сообщения/вопроса не может быть пустым")
        if self.next and not NODE_ID.fullmatch(self.next):
            raise ValueError("Некорректный ID следующего блока")
        if self.kind == "choice" and not self.options:
            raise ValueError("Блок выбора должен содержать хотя бы одну кнопку")
        if self.kind in {"photo", "document"}:
            media = (self.media or "").strip()
            if not (media.startswith("https://") and " " not in media or FILE_ID.fullmatch(media)):
                raise ValueError("Для фото/документа нужен HTTPS URL или Telegram file_id")
        if self.kind in {"input", "condition", "set_variable"} and (
            not self.variable or not NODE_ID.fullmatch(self.variable)
        ):
            raise ValueError("Invalid variable name")
        if self.kind == "condition":
            if not self.true_target or not self.false_target:
                raise ValueError("Condition requires true and false targets")
            if self.next:
                raise ValueError("Condition uses branches instead of next")
        if self.kind in {"input", "set_variable"} and not self.next:
            raise ValueError("Input/variable node requires next")
        if self.kind == "end" and self.next:
            raise ValueError("Завершающий блок не может иметь продолжение")
        return self


class Scenario(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    start: str = Field(min_length=1, max_length=40)
    nodes: list[ScenarioNode] = Field(min_length=1, max_length=80)

    @model_validator(mode="after")
    def validate_graph(self):
        ids = [node.id for node in self.nodes]
        if len(set(ids)) != len(ids):
            raise ValueError("ID блоков должны быть уникальны")
        if self.start not in ids:
            raise ValueError("Начальный блок отсутствует в схеме")
        existing = set(ids)
        for node in self.nodes:
            if node.next and node.next not in existing:
                raise ValueError(f"Блок {node.id}: переход на отсутствующий блок {node.next}")
            for dest in (node.true_target, node.false_target):
                if dest and dest not in existing:
                    raise ValueError(f"Node {node.id}: condition target missing: {dest}")
            for option in node.options:
                if option.target not in existing:
                    raise ValueError(f"Блок {node.id}: кнопка ведёт в неизвестный блок {option.target}")
        return self


def _reachable(scenario: Scenario) -> set[str]:
    by_id = {node.id: node for node in scenario.nodes}
    found = set()
    queue = deque([scenario.start])
    while queue:
        current = queue.popleft()
        if current in found:
            continue
        found.add(current)
        node = by_id[current]
        if node.next:
            queue.append(node.next)
        if node.kind == "choice":
            queue.extend(option.target for option in node.options)
        if node.kind == "condition":
            queue.extend((node.true_target, node.false_target))
    return found


@router.get("/capabilities")
def capabilities():
    return {
        "name": "OmniFactory Telegram Workflow Builder",
        "supported_blocks": ["message", "choice", "photo", "document", "end", "input", "condition", "set_variable"],
        "validation": True,
        "export": "aiogram 3 Python project ZIP",
        "server_persistence": True,
        "persistence_requires_account": True,
        "live_deployment": False,
    }


# Discovery catalog. Availability is intentionally explicit: listings do not imply
# OAuth connections or workflow execution are implemented.
INTEGRATION_CATALOG = (
    {"id": "telegram", "name": "Telegram", "category": "messaging",
     "status": "export", "blocks": ["message", "choice", "photo", "document", "end", "input", "condition", "set_variable"],
     "description": "Генерация Python / aiogram 3 сценария"},
    {"id": "google_docs", "name": "Google Docs", "category": "documents",
     "status": "planned", "blocks": ["create_document", "append_text", "read_document"],
     "description": "Для работы потребуются Google OAuth и серверный исполнитель"},
    {"id": "google_sheets", "name": "Google Sheets", "category": "documents",
     "status": "planned", "blocks": ["read_rows", "append_row", "update_row"],
     "description": "Для работы потребуются Google OAuth и серверный исполнитель"},
    {"id": "facebook", "name": "Facebook Pages", "category": "social",
     "status": "planned", "blocks": ["publish_post", "read_comments", "page_message"],
     "description": "Потребуются Meta Graph API, разрешения и OAuth"},
    {"id": "instagram", "name": "Instagram Business", "category": "social",
     "status": "planned", "blocks": ["publish_media", "list_comments", "reply_comment"],
     "description": "Потребуются Meta Instagram API, разрешения и OAuth"},
    {"id": "http", "name": "HTTP / REST", "category": "logic",
     "status": "planned", "blocks": ["request", "webhook"],
     "description": "Для исполнения нужны ограничения исходящих адресов и контроль секретов"},
    {"id": "python", "name": "Python обработчик", "category": "logic",
     "status": "planned", "blocks": ["handler"],
     "description": "Будет доступен только через изолированный исполнитель"},
)


@router.get("/integrations")
def list_integrations():
    """Public, non-secret integration catalog with honest capability flags."""
    return {"integrations": list(INTEGRATION_CATALOG),
            "statuses": {"export": "Работает экспорт", "planned": "В разработке"}}


VARIABLE_RE = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]{0,39})\}\}")


def substitute(template: str, variables: dict[str, str]) -> str:
    """Render only explicit variable placeholders, never Python expressions."""
    return VARIABLE_RE.sub(lambda match: variables.get(match.group(1), ""), template)


def match_condition(actual: str, operator: str, expected: str) -> bool:
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "contains":
        return expected in actual
    if operator == "not_empty":
        return bool(actual.strip())
    return False


class SimulationRequest(BaseModel):
    """Bounded dry-run. No Telegram calls, network, credentials or user code."""

    scenario: Scenario
    choices: dict[str, int] = Field(default_factory=dict, max_length=80)
    inputs: dict[str, str] = Field(default_factory=dict, max_length=80)


@router.post("/simulate")
def simulate_scenario(request: SimulationRequest):
    """Bounded, deterministic server-side dry run with per-step state snapshots.

    Trace rows are enriched with before/after variables and chosen next node,
    allowing the editor to display an actual interpreter trace. No user code
    or integration is executed; snapshots are per-request and not persisted.
    """
    scenario = request.scenario
    by_id = {node.id: node for node in scenario.nodes}
    trace: list[dict] = []
    variables: dict[str, str] = {}
    current = scenario.start

    def finish(state: str, **extra):
        return {"status": state, "trace": trace, "steps": len(trace),
                "variables": dict(variables), **extra}

    for _ in range(50):
        node = by_id[current]
        item = {
            "id": node.id, "kind": node.kind,
            "text": substitute(node.text, variables),
            "variables_before": dict(variables),
        }
        if node.kind in {"photo", "document"}:
            item["media"] = node.media
        trace.append(item)

        def step_done(next_id: str | None = None, *, row: dict = item):
            row["variables_after"] = dict(variables)
            row["next"] = next_id

        if node.kind == "end":
            step_done()
            return finish("completed")
        if node.kind == "set_variable":
            variables[node.variable] = substitute(node.value, variables)
            current = node.next
            step_done(current)
            continue
        if node.kind == "input":
            value = request.inputs.get(node.id)
            if value is None:
                step_done()
                return finish("awaiting_input", at=node.id, variable=node.variable)
            if not value.strip() or len(value) > 300:
                step_done()
                return finish("invalid_input", at=node.id)
            variables[node.variable] = value
            current = node.next
            step_done(current)
            continue
        if node.kind == "condition":
            actual = variables.get(node.variable, "")
            expected = substitute(node.value, variables)
            outcome = match_condition(actual, node.operator, expected)
            item["result"] = outcome
            current = node.true_target if outcome else node.false_target
            step_done(current)
            continue
        if node.kind == "choice":
            index = request.choices.get(node.id)
            if index is None:
                step_done()
                return finish(
                    "awaiting_choice", at=node.id,
                    options=[{"index": i, "label": option.label}
                             for i, option in enumerate(node.options)],
                )
            if index < 0 or index >= len(node.options):
                step_done()
                return finish("invalid_choice", at=node.id)
            item["selected_option"] = index
            current = node.options[index].target
            step_done(current)
            continue
        if not node.next:
            step_done()
            return finish("completed")
        current = node.next
        step_done(current)

    return finish("step_limit")


def _guaranteed_variables(scenario: Scenario, reachable: set[str]) -> dict[str, set[str]]:
    """Variables initialized on every path reaching each node.

    A forward must-analysis with intersection at joins. Interactive choices
    and conditions create branches; only input/set_variable initialize values.
    """
    nodes = {node.id: node for node in scenario.nodes}
    predecessors: dict[str, set[str]] = {node_id: set() for node_id in reachable}
    all_variables = {
        node.variable for node in scenario.nodes
        if node.kind in {"input", "set_variable"} and node.variable
    }
    for node in scenario.nodes:
        if node.id not in reachable:
            continue
        targets = (
            [option.target for option in node.options] if node.kind == "choice"
            else [node.true_target, node.false_target] if node.kind == "condition"
            else [node.next]
        )
        for target in targets:
            if target in reachable:
                predecessors[target].add(node.id)
    before = {node_id: set(all_variables) for node_id in reachable}
    before[scenario.start] = set()
    after = {node_id: set(all_variables) for node_id in reachable}
    changed = True
    while changed:
        changed = False
        for node_id in sorted(reachable):
            parents = predecessors[node_id]
            incoming = (
                set.intersection(*(after[parent] for parent in parents))
                if parents else set()
            )
            if node_id == scenario.start:
                incoming = set()
            outgoing = incoming.copy()
            node = nodes[node_id]
            if node.kind in {"input", "set_variable"} and node.variable:
                outgoing.add(node.variable)
            if incoming != before[node_id] or outgoing != after[node_id]:
                before[node_id], after[node_id] = incoming, outgoing
                changed = True
    return before


def analyze_scenario(scenario: Scenario) -> dict:
    """Actionable, non-mutating graph diagnostics used by both UI and API."""
    reachable = _reachable(scenario)
    issues = []

    def report(node_id: str, code: str, message: str, severity: str = "warning"):
        issues.append({"node_id": node_id, "code": code,
                       "severity": severity, "message": message})

    assigned = {node.variable for node in scenario.nodes
                if node.kind in {"input", "set_variable"} and node.variable}
    guaranteed = _guaranteed_variables(scenario, reachable)
    placeholders = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]{0,39})\}\}")
    for node in scenario.nodes:
        if node.id not in reachable:
            report(node.id, "unreachable",
                   f"Блок {node.id} недостижим от начального блока")
        if node.id in reachable and node.kind in {"message", "photo", "document", "set_variable"} and not node.next:
            report(node.id, "dead_end",
                   f"Блок {node.id}: нет следующего перехода", "error")
        if node.id in reachable:
            referenced = set(placeholders.findall(node.text))
            if node.kind in {"set_variable", "condition"}:
                referenced.update(placeholders.findall(node.value))
            for name in sorted(referenced - assigned):
                report(node.id, "undefined_variable",
                       f"Блок {node.id}: переменная {{{{{name}}}}} нигде не задаётся")
            for name in sorted((referenced & assigned) - guaranteed[node.id]):
                report(node.id, "variable_may_be_unset",
                       f"Блок {node.id}: переменная {{{{{name}}}}} не задана на всех путях")

    # Fully automatic cycles may exhaust the runtime's 50-step guard.
    # Interactive choice/input nodes are excluded as they wait for the user.
    automatic = {"message", "photo", "document", "set_variable", "condition"}
    by_id = {node.id: node for node in scenario.nodes}
    edges = {}
    for node in scenario.nodes:
        if node.id not in reachable or node.kind not in automatic:
            continue
        targets = ([node.true_target, node.false_target] if node.kind == "condition"
                   else [node.next])
        edges[node.id] = [target for target in targets if target in reachable
                          and by_id[target].kind in automatic]
    visiting, visited, warned = set(), set(), set()

    def visit(node_id: str):
        if node_id in visited:
            return
        visiting.add(node_id)
        for target in edges.get(node_id, []):
            if target in visiting:
                if target not in warned:
                    report(target, "automatic_cycle",
                           f"Блок {target}: цикл без ожидания пользователя", "error")
                    warned.add(target)
            elif target not in visited:
                visit(target)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in edges:
        if node_id not in visited:
            visit(node_id)
    issues.sort(key=lambda item: (item["node_id"], item["code"]))
    return {
        "ok": not any(issue["severity"] == "error" for issue in issues),
        "nodes": len(scenario.nodes),
        "reachable": len(reachable),
        "issues": issues,
        "warnings": [issue["message"] for issue in issues],
        "error_count": sum(issue["severity"] == "error" for issue in issues),
        "warning_count": sum(issue["severity"] == "warning" for issue in issues),
    }


@router.post("/validate")
def validate_scenario(scenario: Scenario):
    return analyze_scenario(scenario)


_RUNTIME_SOURCE = r'''"""Generated by OmniFactory Simple Builder. Python 3.11+, aiogram 3."""
import asyncio
import json
import os
import re
import sqlite3
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

SCENARIO = json.loads((Path(__file__).parent / "scenario.json").read_text(encoding="utf-8"))
NODES = {item["id"]: item for item in SCENARIO["nodes"]}
router = Router()
# Persist dialogue state across process restarts; SQLite is local to this bot.
DB_PATH = Path(os.environ.get("OMNI_STATE_DB", str(Path(__file__).parent / "bot_state.sqlite3")))
CURSORS: dict[tuple[int, int], str] = {}
VALUES: dict[tuple[int, int], dict[str, str]] = {}


def init_state() -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS conversations ("
            "chat_id INTEGER NOT NULL, user_id INTEGER NOT NULL, "
            "cursor TEXT, variables TEXT NOT NULL, "
            "PRIMARY KEY (chat_id, user_id))"
        )
        for chat_id, user_id, cursor, raw in db.execute(
            "SELECT chat_id, user_id, cursor, variables FROM conversations"
        ):
            key = (chat_id, user_id)
            if cursor in NODES:
                CURSORS[key] = cursor
            try:
                values = json.loads(raw)
                if isinstance(values, dict):
                    VALUES[key] = {str(k): str(v) for k, v in values.items()}
            except (ValueError, TypeError):
                VALUES[key] = {}


def save_state(key: tuple[int, int]) -> None:
    with sqlite3.connect(DB_PATH) as db:
        if key not in CURSORS and key not in VALUES:
            db.execute(
                "DELETE FROM conversations WHERE chat_id=? AND user_id=?", key
            )
        else:
            db.execute(
                "INSERT INTO conversations(chat_id,user_id,cursor,variables) "
                "VALUES(?,?,?,?) ON CONFLICT(chat_id,user_id) DO UPDATE SET "
                "cursor=excluded.cursor, variables=excluded.variables",
                (*key, CURSORS.get(key), json.dumps(VALUES.get(key, {}))),
            )

PLACEHOLDER = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]{0,39})\}\}")


def render_text(template: str, values: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda match: values.get(match.group(1), ""), template)


def condition_matches(actual: str, operator: str, expected: str) -> bool:
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "contains":
        return expected in actual
    if operator == "not_empty":
        return bool(actual.strip())
    return False



async def send_node(bot: Bot, chat_id: int, user_id: int, node_id: str) -> None:
    """Send automatic nodes until an interactive choice or the end is reached."""
    cursor_key = (chat_id, user_id)
    values = VALUES.setdefault(cursor_key, {})
    for _ in range(50):
        node = NODES.get(node_id)
        if node is None:
            CURSORS.pop(cursor_key, None)
            save_state(cursor_key)
            await bot.send_message(chat_id, "Ошибка сценария: блок не найден.")
            return
        kind = node["kind"]
        text = render_text(node.get("text") or "", values)
        if kind == "set_variable":
            values[node["variable"]] = render_text(node.get("value", ""), values)
            save_state(cursor_key)
            node_id = node["next"]
            continue
        if kind == "condition":
            actual = values.get(node["variable"], "")
            expected = render_text(node.get("value", ""), values)
            result = condition_matches(actual, node["operator"], expected)
            node_id = node["true_target"] if result else node["false_target"]
            continue
        if kind == "input":
            CURSORS[cursor_key] = node_id
            save_state(cursor_key)
            await bot.send_message(chat_id, text)
            return
        if kind == "choice":
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=choice["label"], callback_data="omni:" + node_id + ":" + str(i))]
                for i, choice in enumerate(node["options"])
            ])
            CURSORS[cursor_key] = node_id
            save_state(cursor_key)
            await bot.send_message(chat_id, text, reply_markup=keyboard)
            return
        if kind == "message":
            await bot.send_message(chat_id, text)
        elif kind == "photo":
            await bot.send_photo(chat_id, photo=node["media"], caption=text or None)
        elif kind == "document":
            await bot.send_document(chat_id, document=node["media"], caption=text or None)
        elif kind == "end":
            if text:
                await bot.send_message(chat_id, text)
            CURSORS.pop(cursor_key, None)
            VALUES.pop(cursor_key, None)
            save_state(cursor_key)
            return
        node_id = node.get("next")
        if not node_id:
            CURSORS.pop(cursor_key, None)
            VALUES.pop(cursor_key, None)
            save_state(cursor_key)
            return
    CURSORS.pop(cursor_key, None)
    VALUES.pop(cursor_key, None)
    save_state(cursor_key)
    await bot.send_message(chat_id, "Обнаружен слишком длинный автоматический цикл. Проверьте схему.")


@router.message(CommandStart())
async def start(message: Message) -> None:
    if message.from_user is None:
        return
    CURSORS.pop((message.chat.id, message.from_user.id), None)
    VALUES.pop((message.chat.id, message.from_user.id), None)
    save_state((message.chat.id, message.from_user.id))
    await send_node(message.bot, message.chat.id, message.from_user.id, SCENARIO["start"])


@router.callback_query(F.data.startswith("omni:"))
async def choose(call: CallbackQuery) -> None:
    try:
        _, node_id, number = (call.data or "").split(":", 2)
        node = NODES[node_id]
        if call.message is None or call.from_user is None:
            raise ValueError("Missing message or user")
        cursor_key = (call.message.chat.id, call.from_user.id)
        if node["kind"] != "choice" or CURSORS.get(cursor_key) != node_id:
            raise ValueError("Expired selection")
        if not number.isascii() or not number.isdecimal():
            raise ValueError("Invalid selection index")
        index = int(number)
        if index >= len(node["options"]):
            raise ValueError("Selection out of bounds")
        target = node["options"][index]["target"]
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        await call.answer("Начните сценарий заново командой /start", show_alert=True)
        return
    # Consume the pending choice *before* awaiting network I/O.
    # Repeated callback taps must not execute the same branch twice.
    CURSORS.pop(cursor_key, None)
    save_state(cursor_key)
    await call.answer()
    await send_node(call.bot, call.message.chat.id, call.from_user.id, target)


@router.message()
async def text_not_expected(message: Message) -> None:
    if message.from_user is None:
        return
    key = (message.chat.id, message.from_user.id)
    current = CURSORS.get(key)
    node = NODES.get(current) if current else None
    if node and node["kind"] == "input":
        value = message.text
        if value is None or not value.strip() or len(value) > 300:
            await message.answer("Отправьте текст до 300 символов.")
            return
        VALUES.setdefault(key, {})[node["variable"]] = value
        CURSORS.pop(key, None)
        save_state(key)
        await send_node(message.bot, message.chat.id, message.from_user.id, node["next"])
        return
    await message.answer("Для выбора используйте кнопки выше либо отправьте /start.")


async def main() -> None:
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Set BOT_TOKEN in your environment before starting bot.py")
    init_state()
    dp = Dispatcher()
    dp.include_router(router)
    bot = Bot(token=token)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
'''
_README = """# Telegram bot generated by OmniFactory

Python 3.11+; aiogram 3. No token is stored in this ZIP.

## Windows PowerShell

    py -3.11 -m venv .venv
    .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
    $env:BOT_TOKEN = "YOUR_NEW_BOT_TOKEN_FROM_BOTFATHER"
    .\\.venv\\Scripts\\python.exe bot.py

Set BOT_TOKEN in your environment/hosting secret manager; never commit it.
Type /start in your Telegram bot to begin the conversation.

## Scope / limitations
- Messages, inline-button choices, photos/documents by HTTPS URL or Telegram
  file_id, and terminal nodes are supported.
- Text input, per-user in-memory variables, {{variable}} substitutions,
  setting values and IF/ELSE comparisons are supported.
- Dialogue positions and variables are stored only in process memory and reset on restart.
- Deploy/hosting, persistent user records, media file upload and CRM integration
  are not part of this export.
- Avoid unconditional message-to-message loops (there is a 50-step guard).
"""


@router.post("/export")
def export_scenario(scenario: Scenario):
    """Return a fixed-template ZIP, never executing user content as Python."""
    diagnosis = analyze_scenario(scenario)
    if not diagnosis["ok"]:
        raise HTTPException(status_code=422, detail={
            "message": "Исправьте ошибки графа перед экспортом",
            "issues": [issue for issue in diagnosis["issues"]
                       if issue["severity"] == "error"],
        })
    # Bound file sizes: max 80 nodes, constrained text and options via Pydantic.
    payload = json.dumps(scenario.model_dump(mode="json"), ensure_ascii=False, indent=2)
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as output:
        output.writestr("scenario.json", payload)
        output.writestr("bot.py", _RUNTIME_SOURCE)
        output.writestr("requirements.txt", "aiogram>=3.0,<4.0\n")
        output.writestr(".env.example", "BOT_TOKEN=YOUR_BOTFATHER_TOKEN\n")
        output.writestr("README.md", _README)
    mem.seek(0)
    return StreamingResponse(
        mem, media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="omnifactory_telegram_bot.zip"',
                 "Cache-Control": "no-store"}
    )
