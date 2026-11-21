"""Self-contained, reproducible Blueprint project handoff archive.

A delivery package is a planning artifact, not deployable software. It contains
no secrets, uploaded data, network calls or server-side state.
"""
from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from hashlib import sha256

from omni_site.blueprint_specification import compile_specification
from omni_site.blueprint_project_plan import build_project_plan


@dataclass(frozen=True)
class DeliveryPackage:
    revision: str
    content: bytes


def make_delivery_package(
    *,
    sector: str,
    team: str,
    process: str,
    priority: str,
    integrations: tuple[str, ...] = (),
) -> DeliveryPackage:
    spec = compile_specification(
        sector=sector, team=team, process=process, priority=priority,
        integrations=integrations,
    )
    chosen = sorted(integrations)
    plan = build_project_plan(spec)
    config = {
        "schema": "omnifactory.blueprint.package.v1",
        "revision": spec.revision,
        "status": "draft",
        "deployable": False,
        "sector": sector,
        "team": team,
        "process": process,
        "priority": priority,
        "integrations": chosen,
    }
    acceptance = {
        "schema": "omnifactory.acceptance.v1",
        "revision": spec.revision,
        "items": [
            {"id": f"AC-{i:03d}", "description": value, "status": "pending"}
            for i, value in enumerate(spec.blueprint.acceptance, 1)
        ],
    }
    checklist = (
        "# Передача проекта / контрольный список\n\n"
        "- [ ] Уточнены требования и границы MVP\n"
        "- [ ] Подтверждены права доступа и ответственные\n"
        "- [ ] Согласованы API-контракты и источники данных\n"
        "- [ ] Проверены резервирование, восстановление и миграции\n"
        "- [ ] Согласованы критерии приёмки\n"
        "- [ ] Подписано отдельное техническое задание\n\n"
        "Это предварительный пакет для обсуждения, не рабочий код.\n"
    )
    files = {
        "README.md": (
            "# OMNIFACTORY / Blueprint delivery package\n\n"
            f"Revision: `{spec.revision}`\n\n"
            "Содержимое: предварительное ТЗ, конфигурация, "
            "критерии приёмки, контрольный список и SHA-256 manifest.\n"
            "Архив не содержит готового приложения и не запускает интеграции.\n"
        ),
        "SPECIFICATION.md": spec.markdown,
        "blueprint.json": json.dumps(
            config, ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n",
        "acceptance.json": json.dumps(
            acceptance, ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n",
        "CHECKLIST.md": checklist,
        "architecture.json": json.dumps(
            plan.architecture, ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n",
        "milestones.json": json.dumps(
            plan.milestones, ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n",
        "verification.json": json.dumps(
            plan.verification, ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n",
        "risks.json": json.dumps(
            plan.risks, ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n",
    }
    encoded = {
        name: value.encode("utf-8") for name, value in sorted(files.items())
    }
    manifest = {
        "schema": "omnifactory.delivery.manifest.v1",
        "revision": spec.revision,
        "files": {
            name: {"sha256": sha256(data).hexdigest(), "bytes": len(data)}
            for name, data in encoded.items()
        },
    }
    encoded["manifest.json"] = (
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(encoded.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return DeliveryPackage(revision=spec.revision, content=buffer.getvalue())
