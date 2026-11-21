"""Safe, read-only connector configuration diagnostics.

Checks effective operator gates and workflow node configuration without calling
third-party services. Never returns credential names, values or input payloads.
"""
from __future__ import annotations

import os
import re
from urllib.parse import urlparse

from automation.engine import WorkflowDefinition

CONNECTOR_KINDS = ("google_docs", "google_sheets", "facebook_page", "instagram", "http")
LABELS = {
    "google_docs": "Google Docs",
    "google_sheets": "Google Sheets",
    "facebook_page": "Facebook Pages",
    "instagram": "Instagram",
    "http": "HTTPS API",
}
ACTIONS = {
    "google_docs": "create",
    "google_sheets": "append",
    "facebook_page": "publish",
    "instagram": "publish_image",
}


def _gate(kind: str) -> list[str]:
    missing = []
    if os.getenv("OMNI_AUTOMATION_LIVE_ENABLED") != "1":
        missing.append("platform_live_disabled")
    if kind == "http":
        if os.getenv("OMNI_AUTOMATION_HTTP_LIVE_ENABLED") != "1":
            missing.append("http_live_disabled")
        if not os.getenv("OMNI_AUTOMATION_EGRESS_PROXY"):
            missing.append("egress_proxy_missing")
        if not os.getenv("OMNI_AUTOMATION_ALLOWED_HOSTS", "").strip():
            missing.append("host_allowlist_missing")
    return missing


def _node_issues(kind: str, config: dict) -> list[str]:
    issues = []
    if kind != "http" and config.get("action") != ACTIONS[kind]:
        issues.append("unsupported_action")
    credential = config.get("credential")
    if credential:
        if not os.getenv(credential):
            issues.append("credential_not_configured")
    elif kind != "http":
        issues.append("credential_reference_missing")
    if kind == "http":
        url = str(config.get("url", ""))
        parsed = urlparse(url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                or parsed.password or parsed.port not in (None, 443)):
            issues.append("https_destination_invalid")
        else:
            allow = {x.strip().lower() for x in
                     os.getenv("OMNI_AUTOMATION_ALLOWED_HOSTS", "").split(",") if x.strip()}
            if parsed.hostname.lower().rstrip(".") not in allow:
                issues.append("destination_not_allowlisted")
        if config.get("method", "GET") not in {"GET", "POST"}:
            issues.append("unsupported_http_method")
    elif kind == "google_sheets":
        if not re.fullmatch(r"[A-Za-z0-9_-]{20,100}", str(config.get("spreadsheet_id", ""))):
            issues.append("spreadsheet_id_invalid")
        rows = config.get("rows", [])
        if not isinstance(rows, list) or len(rows) > 25 or any(
            not isinstance(row, list) or len(row) > 20 for row in rows
        ):
            issues.append("rows_invalid")
    elif kind == "facebook_page":
        page = str(config.get("page_id", ""))
        if not page.isdecimal() or len(page) > 40:
            issues.append("page_id_invalid")
        message = config.get("message", "")
        if not isinstance(message, str) or not 1 <= len(message) <= 4000:
            issues.append("message_invalid")
    elif kind == "instagram":
        account = str(config.get("account_id", ""))
        if not account.isdecimal() or len(account) > 40:
            issues.append("account_id_invalid")
        if not str(config.get("image_url", "")).startswith("https://"):
            issues.append("media_url_invalid")
    return issues


def diagnose(definition: WorkflowDefinition) -> dict:
    """Validate readiness, not connectivity or provider permissions."""
    nodes = []
    for node in definition.nodes:
        if node.kind not in CONNECTOR_KINDS:
            continue
        reasons = list(dict.fromkeys(_gate(node.kind) + _node_issues(node.kind, node.config)))
        nodes.append({
            "node_id": node.id,
            "kind": node.kind,
            "label": LABELS[node.kind],
            "status": "configuration_blocked" if reasons else "configuration_ready",
            "reasons": reasons,
            "network_tested": False,
            "permissions_verified": False,
        })
    return {
        "mode": "configuration_only",
        "network_calls": 0,
        "external_permissions_verified": False,
        "nodes": nodes,
        "ready": sum(node["status"] == "configuration_ready" for node in nodes),
        "blocked": sum(node["status"] == "configuration_blocked" for node in nodes),
    }


def operator_overview() -> dict:
    """Gate overview; credential presence is assessed per workflow node."""
    return {
        "mode": "configuration_only",
        "network_calls": 0,
        "connectors": [
            {
                "kind": kind,
                "label": LABELS[kind],
                "status": "operator_gate_ready" if not _gate(kind) else "operator_gate_blocked",
                "reasons": _gate(kind),
                "permissions_verified": False,
                "network_tested": False,
            }
            for kind in CONNECTOR_KINDS
        ],
    }
