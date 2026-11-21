"""Turn a Telegram Blueprint into a real saved Graph Studio scenario.

The generated graph is executable/exportable through the existing simple builder,
not a pretend deployment. Other Blueprint sectors are deliberately rejected.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from api.builder_projects import ProjectData, create_project
from api.simple_builder import Scenario
from omni_site.blueprint_export import BlueprintInput
from omni_site.blueprint_studio import make_blueprint

router = APIRouter(tags=["Blueprint → Graph Studio"])


class BlueprintProjectInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    blueprint: BlueprintInput
    name: str = Field(min_length=2, max_length=100)


def build_telegram_graph(payload: BlueprintProjectInput) -> ProjectData:
    if payload.blueprint.sector != "telegram":
        raise HTTPException(
            status_code=422,
            detail="Graph Studio exports Telegram workflows only; CRM and automation "
                   "blueprints require their own project types",
        )
    try:
        brief = make_blueprint(
            sector=payload.blueprint.sector,
            team=payload.blueprint.team,
            process=payload.blueprint.process,
            priority=payload.blueprint.priority,
            integrations=tuple(payload.blueprint.integrations),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # A complete, reachable and editable aiogram scenario. All branches terminate.
    scenario = Scenario.model_validate({
        "name": payload.name,
        "start": "welcome",
        "nodes": [
            {
                "id": "welcome",
                "kind": "message",
                "text": "Добро пожаловать! " + brief.title,
                "next": "choose",
            },
            {
                "id": "choose",
                "kind": "choice",
                "text": "Что вы хотите сделать?",
                "options": [
                    {"label": "Оставить заявку", "target": "request"},
                    {"label": "Узнать подробнее", "target": "details"},
                ],
            },
            {
                "id": "request",
                "kind": "input",
                "text": "Опишите ваш запрос одним сообщением.",
                "variable": "request_text",
                "next": "received",
            },
            {
                "id": "received",
                "kind": "message",
                "text": "Ваш запрос: {{request_text}}",
                "next": "finish",
            },
            {
                "id": "details",
                "kind": "message",
                "text": brief.objective,
                "next": "finish",
            },
            {"id": "finish", "kind": "end"},
        ],
    })
    return ProjectData(
        scenario=scenario,
        positions={
            "welcome": {"x": 100, "y": 120},
            "choose": {"x": 380, "y": 120},
            "request": {"x": 680, "y": 40},
            "received": {"x": 960, "y": 40},
            "details": {"x": 680, "y": 260},
            "finish": {"x": 1240, "y": 140},
        },
    )


@router.post("/api/v1/blueprint/projects", status_code=201)
def save_blueprint_as_project(request: Request, payload: BlueprintProjectInput):
    """Use the existing account-scoped, CSRF-verified, transactional save path."""
    data = build_telegram_graph(payload)
    return create_project(request, data)
