"""Independent release gate for generated Telegram bot ZIPs.

Verifies the actual archive bytes rather than trusting preflight alone.
No bot execution, Telegram requests, filesystem writes, or secret exposure.
"""
from __future__ import annotations

import base64
import io
import json
import zipfile

from runtime.telegram.scenario import read_scenario

REQUIRED_FILES = frozenset({
    "scenario.json", "bot.py", "requirements.txt", ".env.example", "README.md",
})
MAX_ARCHIVE_BYTES = 500_000
MAX_MEMBER_BYTES = 300_000


class ExportContractError(ValueError):
    """The generated ZIP violates the supported runnable export contract."""


def verify_export_archive(archive_bytes: bytes) -> dict:
    if not archive_bytes or len(archive_bytes) > MAX_ARCHIVE_BYTES:
        raise ExportContractError("Export ZIP missing or exceeds size limit")
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or set(names) != REQUIRED_FILES:
                raise ExportContractError("Unexpected or duplicate ZIP members")
            for info in archive.infolist():
                if info.file_size > MAX_MEMBER_BYTES:
                    raise ExportContractError("ZIP member exceeds size limit")
                if info.flag_bits & 0x1:
                    raise ExportContractError("Encrypted ZIP member is unsupported")
            scenario_bytes = archive.read("scenario.json")
            source_bytes = archive.read("bot.py")
            requirements = archive.read("requirements.txt").decode("utf-8")
            env_example = archive.read(".env.example").decode("utf-8")
            readme = archive.read("README.md").decode("utf-8")
    except (zipfile.BadZipFile, UnicodeError, OSError, RuntimeError) as exc:
        raise ExportContractError("Unreadable generated archive") from exc
    try:
        scenario = read_scenario(base64.b64encode(scenario_bytes).decode("ascii"))
        compile(source_bytes, "bot.py", "exec")
        parsed = json.loads(scenario_bytes.decode("utf-8"))
    except (ValueError, SyntaxError, UnicodeError, TypeError) as exc:
        raise ExportContractError("Invalid scenario or generated Python runtime") from exc
    if parsed != scenario:
        raise ExportContractError("Scenario changed during validation")
    if "aiogram" not in requirements or "BOT_TOKEN" not in env_example:
        raise ExportContractError("Missing runtime dependency or token placeholder")
    if "OMNI_STATE_DB" not in readme or "OMNI_STATE_DB" not in source_bytes.decode("utf-8"):
        raise ExportContractError("Persistence contract missing")
    if "YOUR_BOTFATHER_TOKEN" not in env_example:
        raise ExportContractError("Expected placeholder token, not a real credential")
    return {
        "verified": True,
        "files": sorted(names),
        "nodes": len(scenario["nodes"]),
        "scenario_name": scenario.get("name"),
        "python_compiles": True,
        "runtime_scenario_compatible": True,
        "telegram_delivery_verified": False,
        "cloud_deployed": False,
    }
