"""Acceptance contract for exported aiogram ZIP and its documentation."""
import asyncio
import io
import json
import zipfile

from api.simple_builder import Scenario, export_scenario


def test_export_zip_contains_runnable_runtime_and_correct_persistence_docs():
    scenario = Scenario.model_validate({
        "name": "Acceptance",
        "start": "start",
        "nodes": [
            {"id": "start", "kind": "message", "text": "Привет", "next": "end"},
            {"id": "end", "kind": "end"},
        ],
    })
    response = export_scenario(scenario)

    async def collect():
        return b"".join([chunk async for chunk in response.body_iterator])

    payload = asyncio.run(collect())
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert set(archive.namelist()) == {
            "scenario.json", "bot.py", "requirements.txt", ".env.example", "README.md",
            "Dockerfile", "railway.json", "DEPLOY_RAILWAY.md", "smoke.py",
        }
        bot = archive.read("bot.py").decode("utf-8")
        readme = archive.read("README.md").decode("utf-8")
        exported = json.loads(archive.read("scenario.json"))
        assert exported["start"] == "start"
        compile(bot, "bot.py", "exec")
        assert "init_state()" in bot
        assert "save_state(" in bot
        assert "OMNI_STATE_DB" in bot
        assert "bot_state.sqlite3" in readme
        assert "OMNI_STATE_DB" in readme
        assert "reset on restart" not in readme
        assert "BOT_TOKEN" in archive.read(".env.example").decode("utf-8")
