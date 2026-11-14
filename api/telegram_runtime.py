"""Owner-only scenario compatibility report for isolated Telegram runtime.

The scenario never contains BotFather tokens. The runtime's future worker
will inject encrypted secrets and selected scenario through separate channels.
"""
from __future__ import annotations

import base64
import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from automation.release_gate import allowed_image, scenario_sha256
from portal.db import session_factory
from portal.models import BuilderProject
from portal.routes import current_customer
from portal.security import secure_request
from runtime.telegram.scenario import read_scenario

router = APIRouter(prefix="/api/v1/cloud/runtime", tags=["Telegram Runtime"])


@router.get("/capabilities")
def capabilities():
    return {
        "runtime": "telegram_aiogram",
        "transport": "webhook",
        "scenario_validation": True,
        "secret_header_check": True,
        "process_health": True,
        "persistent_conversation_state": False,
        "update_deduplication": False,
        "live_railway_deploy_enabled": False,
        "can_claim_bot_online": False,
    }


@router.get("/preflight/{bot_id}")
def preflight(bot_id: UUID, request: Request):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            raise HTTPException(401, "Sign in to inspect your bot")
        project = db.scalar(select(BuilderProject).where(
            BuilderProject.id == str(bot_id),
            BuilderProject.customer_id == user.id))
        if project is None:
            raise HTTPException(404, "Bot not found")
        try:
            raw = project.scenario_json.encode("utf-8")
            scenario = read_scenario(base64.b64encode(raw).decode("ascii"))
            # Configuration is checked against the selected immutable runtime,
            # not returned in an API response or stored in deployment jobs.
            valid = True
            issue = None
            node_types = sorted({n["kind"] for n in scenario["nodes"]})
            sha = scenario_sha256(project.scenario_json)
        except (ValueError, KeyError, TypeError):
            valid = False
            issue = "Scenario is not compatible with Telegram Runtime v1"
            node_types = []
            sha = None
        image = allowed_image("telegram_aiogram")
        return {
            "project_id": project.id,
            "name": project.name,
            "scenario_compatible": valid,
            "issue": issue,
            "scenario_sha256": sha,
            "nodes": len(scenario["nodes"]) if valid else None,
            "node_types": node_types,
            "image_digest_configured": bool(image),
            "image": image,
            "runtime_state": "single_replica_in_memory",
            "verified_telegram_delivery": False,
            "production_ready": False,
            "requires": [
                "Durable conversation state and update deduplication",
                "Signed image and vulnerability provenance",
                "Isolated secret injection worker",
                "Verified provider budget and user agreement",
                "Telegram webhook registration and end-to-end delivery test",
            ],
        }
