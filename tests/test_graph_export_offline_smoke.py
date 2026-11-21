"""Execute the generated bot's offline smoke test without Telegram or secrets."""
import io
import subprocess
import sys
import zipfile

from fastapi.testclient import TestClient

from server import app

CLIENT = TestClient(app)
SCENARIO = {
    "name": "Restart-safe bot",
    "start": "start",
    "nodes": [
        {"id": "start", "kind": "message", "text": "Hello", "next": "choose"},
        {"id": "choose", "kind": "choice", "text": "Continue?", "options": [
            {"label": "Yes", "target": "finish"},
            {"label": "No", "target": "finish"},
        ]},
        {"id": "finish", "kind": "end"},
    ],
}


def test_exported_bot_runs_offline_smoke_with_sqlite_restart(tmp_path):
    response = CLIENT.post("/api/v1/builder/simple/export", json=SCENARIO)
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        for filename in ("bot.py", "scenario.json", "smoke.py"):
            (tmp_path / filename).write_bytes(archive.read(filename))
    process = subprocess.run(
        [sys.executable, "smoke.py"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    assert "OMNIFACTORY_SMOKE_OK" in process.stdout
    assert not (tmp_path / "bot_state.sqlite3").exists()
