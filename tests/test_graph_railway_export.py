"""Runnable Telegram export includes verified Railway worker artifacts."""
import io
import json
import zipfile

from fastapi.testclient import TestClient

from api.export_contract import ExportContractError, verify_export_archive
from server import app

client = TestClient(app)
SCENARIO = {
    "name": "Railway-ready Telegram bot",
    "start": "hello",
    "nodes": [
        {"id": "hello", "kind": "message", "text": "Hello!", "next": "finish"},
        {"id": "finish", "kind": "end"},
    ],
}


def test_export_contains_runnable_worker_and_persistent_state_contract():
    response = client.post("/api/v1/builder/simple/export", json=SCENARIO)
    assert response.status_code == 200, response.text
    report = verify_export_archive(response.content)
    assert report["verified"] is True
    assert report["railway_worker_packaged"] is True
    assert report["persistent_volume_required"] is True
    assert report["cloud_deployed"] is False
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        dockerfile = archive.read("Dockerfile").decode()
        railway = json.loads(archive.read("railway.json"))
        assert "RUN python smoke.py" in dockerfile
        assert "USER omni" in dockerfile
        assert "OMNI_STATE_DB=/data/bot_state.sqlite3" in dockerfile
        assert railway["build"]["builder"] == "DOCKERFILE"
        assert "healthcheckPath" not in railway["deploy"]
        assert "/data" in archive.read("DEPLOY_RAILWAY.md").decode()
        assert "BOT_TOKEN" not in dockerfile


def test_archive_contract_rejects_missing_deployment_files():
    response = client.post("/api/v1/builder/simple/export", json=SCENARIO)
    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        files = {
            name: archive.read(name)
            for name in archive.namelist()
            if name != "Dockerfile"
        }
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w") as archive:
        for name, value in files.items():
            archive.writestr(name, value)
    try:
        verify_export_archive(result.getvalue())
    except ExportContractError:
        pass
    else:
        raise AssertionError("Missing Dockerfile must fail verification")
