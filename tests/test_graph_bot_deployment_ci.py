"""Generated Telegram bot ships an independent, runnable CI pipeline."""
import asyncio
import io
import zipfile

from api.export_contract import ExportContractError, verify_export_archive
from api.simple_builder import Scenario, export_scenario


def exported():
    scenario = Scenario.model_validate({
        "name": "Generated CI bot",
        "start": "hello",
        "nodes": [
            {"id": "hello", "kind": "message", "text": "Hello", "next": "finish"},
            {"id": "finish", "kind": "end"},
        ],
    })
    response = export_scenario(scenario)

    async def collect():
        return b"".join([chunk async for chunk in response.body_iterator])

    return asyncio.run(collect())


def test_exported_workflow_checks_real_bot_and_docker():
    payload = exported()
    report = verify_export_archive(payload)
    assert report["github_ci_packaged"] is True
    assert report["cloud_deployed"] is False
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        workflow = archive.read(".github/workflows/verify.yml").decode()
        guide = archive.read("DEPLOY_RAILWAY.md").decode()
        assert "python -m py_compile bot.py smoke.py" in workflow
        assert "run: python smoke.py" in workflow
        assert "run: docker build --tag omni-generated-bot:ci ." in workflow
        assert "pull_request:" in workflow
        assert "contents: read" in workflow
        assert "GitHub Actions" in guide
        assert "BOT_TOKEN" not in workflow


def test_missing_workflow_fails_closed():
    payload = exported()
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(payload)) as source:
        with zipfile.ZipFile(output, "w") as target:
            for name in source.namelist():
                if name != ".github/workflows/verify.yml":
                    target.writestr(name, source.read(name))
    try:
        verify_export_archive(output.getvalue())
    except ExportContractError as exc:
        assert "Unexpected" in str(exc)
    else:
        raise AssertionError("Missing generated CI must fail the export contract")
