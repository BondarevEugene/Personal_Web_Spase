"""Versioned, bounded, non-persistent Blueprint handoff contract."""
from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from omni_site.blueprint_studio import make_blueprint

router = APIRouter(tags=["Blueprint export"])


class BlueprintInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sector: Literal["crm", "telegram", "automation"]
    team: Literal["solo", "growth", "enterprise"]
    process: Literal["new", "manual", "legacy"]
    priority: Literal["control", "speed", "scale"]
    integrations: list[str] = Field(default_factory=list, max_length=4)


@router.post("/api/v1/blueprint/export")
def export_blueprint(payload: BlueprintInput):
    """Return a portable planning document, not a deployed or saved project."""
    try:
        brief = make_blueprint(
            sector=payload.sector,
            team=payload.team,
            process=payload.process,
            priority=payload.priority,
            integrations=tuple(payload.integrations),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    document = {
        "schema": "omnifactory.blueprint.v1",
        "kind": "planning_brief",
        "saved": False,
        "deployable": False,
        "input": payload.model_dump(),
        "blueprint": asdict(brief),
    }
    return JSONResponse(
        document,
        headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"},
    )
