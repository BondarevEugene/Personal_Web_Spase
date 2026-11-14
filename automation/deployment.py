"""Provider-neutral deployment planning for OmniFactory Managed Cloud.

Planning does not create billable infrastructure. A separate, audited
provisioning worker will later consume approved plans. No credentials are
accepted from clients in a deployment manifest.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

IDENT = re.compile(r"^[a-z][a-z0-9-]{2,38}$")
CONFIG_KEYS = {"BOT_TOKEN", "DATABASE_URL", "WEBHOOK_SECRET", "OPENAI_API_KEY"}
RUNTIME_IMAGES = {"telegram_aiogram": "omnifactory/telegram-runtime",
                  "automation": "omnifactory/automation-runtime"}


class DeploymentSpec(BaseModel):
    name: str = Field(min_length=3, max_length=40)
    runtime: Literal["telegram_aiogram", "automation"]
    mode: Literal["managed", "byoc"] = "managed"
    provider: Literal["railway", "cloud_run"] = "railway"
    transport: Literal["webhook", "worker"] = "webhook"
    version: str = Field(min_length=8, max_length=100)
    region: str | None = Field(default=None, max_length=60)
    max_monthly_usd: int = Field(ge=5, le=10000)
    secret_refs: list[str] = Field(default_factory=list, max_length=12)
    workflow_id: str | None = None

    @model_validator(mode="after")
    def check_spec(self):
        if not IDENT.fullmatch(self.name):
            raise ValueError("Name must be lowercase letters/digits/hyphens")
        if self.runtime == "telegram_aiogram" and self.transport not in {"worker", "webhook"}:
            raise ValueError("Unsupported Telegram transport")
        if self.runtime == "automation" and self.transport != "webhook":
            raise ValueError("Automation API requires webhook transport")
        if self.mode == "managed" and self.provider != "railway":
            raise ValueError("Managed Cloud v1 is Railway-only")
        if self.mode == "byoc" and self.provider != "railway":
            raise ValueError("BYOC v1 requires Railway OAuth integration")
        if not re.fullmatch(r"[A-Za-z0-9_.-]{8,100}", self.version):
            raise ValueError("Version must be a pinned release identifier")
        if len(set(self.secret_refs)) != len(self.secret_refs) or any(
            not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", ref)
            or ref not in CONFIG_KEYS for ref in self.secret_refs
        ):
            raise ValueError("Unsupported secret reference")
        if self.workflow_id and not re.fullmatch(r"[0-9a-fA-F-]{36}", self.workflow_id):
            raise ValueError("Invalid workflow identifier")
        return self


class DeploymentPlan(BaseModel):
    spec: DeploymentSpec
    manifest_sha256: str
    steps: list[str]
    warnings: list[str]
    state: Literal["planned"] = "planned"
    estimated_usd: None = None
    creates_resources: bool = False
    next_action: str = "Review permissions, secrets and projected cost"


def build_plan(spec: DeploymentSpec) -> DeploymentPlan:
    """Pure deterministic plan, safe to preview without provider tokens."""
    canonical = json.dumps(spec.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    steps = [
        "Validate pinned runtime release and scenario export",
        "Resolve customer-owned secret references in a restricted vault",
        "Verify explicit budget cap and obtain deployment approval",
        f"Provision isolated {spec.provider} project/service via provider adapter",
        "Inject runtime configuration without placing secrets in Git or ZIP",
        "Build or pull immutable runtime image and deploy",
        "Verify healthcheck and Telegram webhook/worker exclusivity",
        "Record deployment status, version, resources and audit event",
    ]
    warnings = [
        "Dry-run plan only: no Railway resources or charges are created.",
        "Cost is not yet estimated: a budget cap is not a cost quote.",
        "Never request Railway account password; use OAuth for BYOC.",
        "Telegram BotFather token must be provided through a secret-vault flow.",
        "No production deployment until provider integration and rollback checks pass.",
    ]
    if spec.transport == "worker":
        warnings.append("Telegram polling worker must be singleton; never run webhook simultaneously.")
    if spec.mode == "managed":
        warnings.append("OMNIFACTORY operates the cloud billing account and must enforce tenant quotas.")
    else:
        warnings.append("BYOC requires an explicit Railway OAuth consent and selected project/workspace scopes.")
    return DeploymentPlan(spec=spec, manifest_sha256=digest, steps=steps, warnings=warnings)


class DeploymentProvider:
    """Minimal capability contract; adapters must not fall back to fake success."""
    name: str

    def readiness(self) -> dict:
        raise NotImplementedError

    def provision(self, *args, **kwargs):
        raise NotImplementedError("Live provisioning is not enabled in Managed Cloud foundation")


class RailwayProvider(DeploymentProvider):
    name = "railway"

    def readiness(self) -> dict:
        from automation.railway_oauth import readiness
        configuration = readiness()
        return {"provider": self.name,
                "oauth_connect": configuration["connection"],
                "graphql_provision": "planned", "deploy": "disabled",
                "mode": "plan_only", "requires_manual_approval": True}


class CloudRunProvider(DeploymentProvider):
    name = "cloud_run"

    def readiness(self) -> dict:
        return {"provider": self.name, "oauth_connect": "not_implemented",
                "deploy": "disabled", "mode": "future"}
