"""Exported ZIP must compile, match isolated runtime and reject broken artifacts."""
import asyncio
import io
import json
import zipfile

import pytest

from api.export_contract import ExportContractError, verify_export_archive
from api.simple_builder import Scenario, export_scenario


def scenario():
    return Scenario.model_validate({
        "name": "Релизный бот",
        "start": "hello",
        "nodes": [
            {"id": "hello", "kind": "message", "text": "Привет", "next": "ask"},
            {"id": "ask", "kind": "choice", "text": "Куда?",
             "options": [{"label": "Да", "target": "yes"},
                         {"label": "Нет", "target": "no"}]},
            {"id": "yes", "kind": "end", "text": "Да"},
            {"id": "no", "kind": "end", "text": "Нет"},
        ],
    })


def exported():
    response = export_scenario(scenario())

    async def collect():
        return b"".join([chunk async for chunk in response.body_iterator])

    return asyncio.run(collect())


def replace_member(blob, filename, contents):
    source = zipfile.ZipFile(io.BytesIO(blob))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as target:
        for name in source.namelist():
            target.writestr(name, contents if name == filename else source.read(name))
    source.close()
    return buffer.getvalue()


def test_exported_archive_is_verified_before_download():
    result = verify_export_archive(exported())
    assert result["verified"]
    assert result["nodes"] == 4
    assert result["python_compiles"]
    assert result["runtime_scenario_compatible"]
    assert result["telegram_delivery_verified"] is False


def test_invalid_python_is_rejected():
    with pytest.raises(ExportContractError, match="Invalid scenario"):
        verify_export_archive(replace_member(exported(), "bot.py", b"def broken("))


def test_missing_target_is_rejected_by_isolated_runtime_validator():
    blob = exported()
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        scenario_data = json.loads(archive.read("scenario.json"))
    scenario_data["nodes"][0]["next"] = "missing"
    changed = replace_member(blob, "scenario.json", json.dumps(scenario_data).encode())
    with pytest.raises(ExportContractError, match="Invalid scenario"):
        verify_export_archive(changed)


def test_archive_with_missing_file_is_rejected():
    blob = exported()
    with zipfile.ZipFile(io.BytesIO(blob)) as source:
        mem = io.BytesIO()
        with zipfile.ZipFile(mem, "w") as target:
            for name in source.namelist():
                if name != "README.md":
                    target.writestr(name, source.read(name))
    with pytest.raises(ExportContractError, match="Unexpected"):
        verify_export_archive(mem.getvalue())


def test_oversized_archive_is_rejected():
    with pytest.raises(ExportContractError, match="size limit"):
        verify_export_archive(b"x" * 500_001)


def test_invalid_placeholder_token_is_rejected():
    with pytest.raises(ExportContractError, match="placeholder"):
        verify_export_archive(replace_member(
            exported(), ".env.example", b"BOT_TOKEN=123456:actualtokenvalue\n"
        ))
