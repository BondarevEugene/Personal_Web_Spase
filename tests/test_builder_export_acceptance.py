"""End-to-end acceptance of the *exported* aiogram bot, without Telegram I/O.

This checks Python ZIP -> import -> /start -> choice -> input -> condition -> end.
It does not rely on platform browser mocks or a real Telegram token.
"""
import asyncio
import importlib.util
import json
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock
from zipfile import ZipFile

from fastapi.testclient import TestClient

from server import app


CLIENT = TestClient(app)
ENDPOINT = "/api/v1/builder/simple/export"
SCENARIO = {
    "name": "Customer onboarding bot",
    "start": "welcome",
    "nodes": [
        {"id": "welcome", "kind": "message", "text": "Welcome!", "next": "choose"},
        {"id": "choose", "kind": "choice", "text": "Proceed?", "options": [
            {"label": "Continue", "target": "ask"},
            {"label": "Quit", "target": "stop"},
        ]},
        {"id": "ask", "kind": "input", "text": "Your name?", "variable": "name",
         "next": "set"},
        {"id": "set", "kind": "set_variable", "variable": "greeting",
         "value": "Hello {{name}}", "next": "condition"},
        {"id": "condition", "kind": "condition", "variable": "name",
         "operator": "not_empty", "value": "",
         "true_target": "success", "false_target": "stop"},
        {"id": "success", "kind": "message", "text": "{{greeting}}", "next": "finish"},
        {"id": "finish", "kind": "end", "text": "Done"},
        {"id": "stop", "kind": "end", "text": "Stopped"},
    ],
}


def exported_module(tmp_path):
    response = CLIENT.post(ENDPOINT, json=SCENARIO)
    assert response.status_code == 200, response.text
    with ZipFile(BytesIO(response.content)) as archive:
        # Verify exact contents and that the export does not contain secrets.
        names = set(archive.namelist())
        assert names == {"bot.py", "scenario.json", "requirements.txt",
                         ".env.example", "README.md",
                         "Dockerfile", "railway.json", "DEPLOY_RAILWAY.md", "smoke.py",
            ".github/workflows/verify.yml"}
        for name in names:
            (tmp_path / name).write_bytes(archive.read(name))
    assert json.loads((tmp_path / "scenario.json").read_text(
        encoding="utf-8"
    ))["start"] == "welcome"
    spec = importlib.util.spec_from_file_location("acceptance_generated_bot", tmp_path / "bot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The production entrypoint initializes SQLite before handling updates.
    # Acceptance tests import handlers directly, so reproduce that bootstrap
    # with an isolated database for each test.
    module.DB_PATH = str(tmp_path / "acceptance_state.sqlite3")
    module.init_state()
    return module


def callback(bot, node_id="choose", index="0"):
    return SimpleNamespace(
        data=f"omni:{node_id}:{index}",
        bot=bot,
        message=SimpleNamespace(chat=SimpleNamespace(id=10)),
        from_user=SimpleNamespace(id=20),
        answer=AsyncMock(),
    )


async def _test_exported_bot_user_journey_and_callback_replay(tmp_path):
    module = exported_module(tmp_path)
    bot = SimpleNamespace(
        send_message=AsyncMock(), send_photo=AsyncMock(), send_document=AsyncMock(),
    )
    user_key = (10, 20)
    message = SimpleNamespace(
        bot=bot, chat=SimpleNamespace(id=10),
        from_user=SimpleNamespace(id=20),
    )
    await module.start(message)
    assert module.CURSORS[user_key] == "choose"
    assert bot.send_message.await_count == 2
    assert bot.send_message.await_args.kwargs["reply_markup"] is not None

    chosen = callback(bot)
    await module.choose(chosen)
    assert module.CURSORS[user_key] == "ask"
    assert chosen.answer.await_count == 1

    # A stale inline button must not execute another route.
    stale = callback(bot)
    count = bot.send_message.await_count
    await module.choose(stale)
    assert bot.send_message.await_count == count
    assert stale.answer.await_args.kwargs["show_alert"] is True

    entry = SimpleNamespace(
        bot=bot, chat=SimpleNamespace(id=10), from_user=SimpleNamespace(id=20),
        text="Alex", answer=AsyncMock(),
    )
    await module.text_not_expected(entry)
    sent_text = [call.args[1] for call in bot.send_message.await_args_list]
    assert sent_text == ["Welcome!", "Proceed?", "Your name?", "Hello Alex", "Done"]
    assert user_key not in module.CURSORS
    # Completed conversations intentionally discard their variables and cursor.
    assert user_key not in module.VALUES

    await module.start(message)
    assert module.CURSORS[user_key] == "choose"
    # A new session starts with an empty variable dictionary.
    assert module.VALUES[user_key] == {}


async def _test_exported_bot_other_choice_finishes_without_input(tmp_path):
    module = exported_module(tmp_path)
    bot = SimpleNamespace(
        send_message=AsyncMock(), send_photo=AsyncMock(), send_document=AsyncMock(),
    )
    user_key = (10, 20)
    await module.send_node(bot, 10, 20, "welcome")
    await module.choose(callback(bot, index="1"))
    assert user_key not in module.CURSORS
    assert bot.send_message.await_args.args[1] == "Stopped"


async def _test_exported_bot_invalid_input_retries_without_state_change(tmp_path):
    module = exported_module(tmp_path)
    bot = SimpleNamespace(
        send_message=AsyncMock(), send_photo=AsyncMock(), send_document=AsyncMock(),
    )
    await module.send_node(bot, 10, 20, "ask")
    entry = SimpleNamespace(
        bot=bot, chat=SimpleNamespace(id=10), from_user=SimpleNamespace(id=20),
        text="   ", answer=AsyncMock(),
    )
    await module.text_not_expected(entry)
    assert module.CURSORS[(10, 20)] == "ask"
    assert "name" not in module.VALUES.get((10, 20), {})
    entry.answer.assert_awaited_once()


def test_generated_runtime_has_no_automatic_cloud_deployment(tmp_path):
    module = exported_module(tmp_path)
    assert not hasattr(module, "deploy_bot")
    assert "BOT_TOKEN" in (tmp_path / "bot.py").read_text(encoding="utf-8")
    assert "Paste API keys" not in (tmp_path / "README.md").read_text(
        encoding="utf-8"
    )

def test_exported_bot_user_journey_and_callback_replay(tmp_path):
    asyncio.run(_test_exported_bot_user_journey_and_callback_replay(tmp_path))


def test_exported_bot_other_choice_finishes_without_input(tmp_path):
    asyncio.run(_test_exported_bot_other_choice_finishes_without_input(tmp_path))


def test_exported_bot_invalid_input_retries_without_state_change(tmp_path):
    asyncio.run(_test_exported_bot_invalid_input_retries_without_state_change(tmp_path))
