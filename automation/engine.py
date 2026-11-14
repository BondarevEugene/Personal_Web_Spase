"""Bounded, explainable OmniFactory workflow engine.

The interpreter never executes arbitrary Python, shell commands, or expressions.
External writes are *simulated by default*. Live connectors use operator-managed
environment credentials and explicit opt-in on the authenticated API.
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel, Field, model_validator

IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,39}$")
TOKEN_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
TEMPLATE = re.compile(r"\{\{([A-Za-z][A-Za-z0-9_-]{0,39})\}\}")
MAX_BYTES = 65536
MAX_STEPS = 50


class WorkflowNode(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    kind: Literal["trigger", "set", "condition", "transform", "http", "google_docs",
                  "google_sheets", "facebook_page", "instagram", "approval", "end"]
    next: str | None = None
    true_target: str | None = None
    false_target: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_node(self):
        if not IDENT.fullmatch(self.id):
            raise ValueError("Invalid node ID")
        if len(json.dumps(self.config, ensure_ascii=False)) > 6000:
            raise ValueError("Node configuration too large")
        # Never accept raw connector credentials as a persisted graph property.
        forbidden = {"access_token", "api_key", "password", "client_secret",
                     "authorization", "bearer_token", "private_key"}
        if any(k.casefold() in forbidden for k in self.config):
            raise ValueError("Secrets must not be embedded in workflow configuration")
        reference = self.config.get("credential")
        if reference and (not isinstance(reference, str) or
                          not TOKEN_NAME.fullmatch(reference) or
                          not reference.startswith("OMNI_CREDENTIAL_")):
            raise ValueError("Credential must be an OMNI_CREDENTIAL_... environment reference")
        for key in (self.next, self.true_target, self.false_target):
            if key is not None and not IDENT.fullmatch(key):
                raise ValueError("Invalid transition ID")
        if self.kind == "condition" and not (self.true_target and self.false_target):
            raise ValueError("Condition requires two branches")
        if self.kind not in {"condition", "end", "approval"} and not self.next:
            raise ValueError("Node requires next transition")
        if self.kind == "end" and (self.next or self.true_target or self.false_target):
            raise ValueError("End cannot have outgoing transitions")
        if self.kind == "approval" and not self.next:
            raise ValueError("Approval requires continuation")
        if self.kind in {"set", "transform", "condition"}:
            name = self.config.get("variable")
            if not isinstance(name, str) or not IDENT.fullmatch(name):
                raise ValueError("Invalid variable name")
        return self


class WorkflowDefinition(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    start: str = Field(min_length=1, max_length=40)
    nodes: list[WorkflowNode] = Field(min_length=1, max_length=80)

    @model_validator(mode="after")
    def graph(self):
        by_id = {n.id: n for n in self.nodes}
        if len(by_id) != len(self.nodes) or self.start not in by_id:
            raise ValueError("Duplicate IDs or start missing")
        for node in self.nodes:
            for dest in (node.next, node.true_target, node.false_target):
                if dest and dest not in by_id:
                    raise ValueError(f"{node.id}: unknown destination {dest}")
        return self


class RunRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)
    live: bool = False
    approval: bool = False


@dataclass
class RunResult:
    status: str
    trace: list[dict[str, Any]]
    variables: dict[str, Any]
    steps: int

    def public(self) -> dict:
        return {"status": self.status, "trace": self.trace,
                "variables": self.variables, "steps": self.steps}


def bounded(value: Any) -> Any:
    try:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("Values must be JSON serializable") from exc
    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Workflow data exceeds 64 KB")
    return value


def substitute(value: Any, variables: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return TEMPLATE.sub(lambda m: str(variables.get(m.group(1), ""))[:2000], value)
    if isinstance(value, list):
        return [substitute(v, variables) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v, variables) for k, v in value.items()}
    return value


def compare(actual: Any, op: str, target: Any) -> bool:
    if op == "equals":
        return actual == target
    if op == "not_equals":
        return actual != target
    if op == "contains":
        return str(target) in str(actual)
    if op == "not_empty":
        return actual not in (None, "", [], {})
    if op == "greater":
        try:
            return float(actual) > float(target)
        except (ValueError, TypeError):
            return False
    if op == "less":
        try:
            return float(actual) < float(target)
        except (ValueError, TypeError):
            return False
    raise ValueError("Unsupported comparison operator")


def public_host(url: str, allow_hosts: set[str]) -> str:
    """No arbitrary local-network requests. Strict HTTPS, host and DNS checks.

    Only an operator may configure allow_hosts; user-supplied workflows cannot
    widen it. DNS rebinding protection requires an egress proxy in production.
    """
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Only HTTPS URLs without credentials/fragments are allowed")
    host = (parsed.hostname or "").lower().rstrip(".")
    if host not in allow_hosts or not host:
        raise ValueError("Destination host not in operator allowlist")
    if parsed.port not in (None, 443):
        raise ValueError("Only HTTPS port 443 is allowed")
    try:
        ipaddress.ip_address(host)
        raise ValueError("IP literals are not permitted")
    except ValueError as exc:
        if "IP literals" in str(exc):
            raise
    try:
        records = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("Destination cannot be resolved") from exc
    if not records or any(
        not ipaddress.ip_address(addr[4][0]).is_global for addr in records
    ):
        raise ValueError("Destination resolves to a restricted address")
    return host


class ConnectorExecutor:
    """Fixed API endpoints; all tokens are operator-managed environment secrets."""

    def __init__(self, *, live: bool):
        self.live = live
        self.requests = 0
        self.max_requests = 3

    def call(self, method: str, url: str, *, token_env: str | None,
             payload: Any = None, allowed: set[str]) -> dict:
        if not self.live:
            return {"mode": "dry_run", "method": method, "host": urlparse(url).hostname}
        if self.requests >= self.max_requests:
            raise ValueError("External-call budget exhausted")
        if os.getenv("OMNI_AUTOMATION_LIVE_ENABLED") != "1":
            raise ValueError("Live execution disabled by platform operator")
        public_host(url, allowed)
        token = None
        if token_env:
            if not TOKEN_NAME.fullmatch(token_env) or not token_env.startswith("OMNI_CREDENTIAL_"):
                raise ValueError("Credential must reference an operator-managed secret")
            token = os.environ.get(token_env)
            if not token:
                raise ValueError("Connector credentials not configured")
        self.requests += 1
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        # All responses streamed and capped. Redirects and environment proxies off.
        try:
            proxy = os.getenv("OMNI_AUTOMATION_EGRESS_PROXY") or None
            with httpx.Client(timeout=6, follow_redirects=False, trust_env=False,
                              proxy=proxy) as client:
                # Meta Graph API expects form fields; Google APIs accept JSON.
                use_form = urlparse(url).hostname == "graph.facebook.com"
                with client.stream(method, url, headers=headers,
                                   data=payload if use_form else None,
                                   json=payload if not use_form else None) as response:
                    if response.status_code >= 300:
                        raise ValueError("Connector returned HTTP " + str(response.status_code))
                    chunks = bytearray()
                    for part in response.iter_bytes():
                        chunks.extend(part)
                        if len(chunks) > MAX_BYTES:
                            raise ValueError("Connector response exceeds 64 KB")
        except httpx.HTTPError as exc:
            raise ValueError("Connector transport failed") from exc
        try:
            return {"status": response.status_code, "data": bounded(json.loads(chunks))}
        except (ValueError, UnicodeError):
            return {"status": response.status_code, "data": chunks.decode("utf-8", "replace")[:2000]}

    def perform(self, node: WorkflowNode, variables: dict[str, Any]) -> dict:
        conf = substitute(node.config, variables)
        kind = node.kind
        if kind == "http":
            url = str(conf.get("url", ""))
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("HTTP node requires an HTTPS destination without credentials")
            hosts = {v.strip().lower() for v in
                     os.getenv("OMNI_AUTOMATION_ALLOWED_HOSTS", "").split(",") if v.strip()}
            if self.live and not hosts:
                raise ValueError("No HTTP destination hosts configured")
            if self.live and (os.getenv("OMNI_AUTOMATION_HTTP_LIVE_ENABLED") != "1" or
                              not os.getenv("OMNI_AUTOMATION_EGRESS_PROXY")):
                raise ValueError("Live custom HTTP requires explicit opt-in and a trusted egress proxy")
            method = conf.get("method", "GET")
            if method not in {"GET", "POST"}:
                raise ValueError("Only GET and POST are supported")
            return self.call(method, url, token_env=conf.get("credential"),
                             payload=conf.get("body"), allowed=hosts)
        if kind == "google_docs":
            if conf.get("action") != "create":
                raise ValueError("Supported Docs action: create")
            return self.call("POST", "https://docs.googleapis.com/v1/documents",
                             token_env=str(conf.get("credential", "")),
                             payload={"title": str(conf.get("title", "Untitled"))[:200]},
                             allowed={"docs.googleapis.com"})
        if kind == "google_sheets":
            if conf.get("action") != "append":
                raise ValueError("Supported Sheets action: append")
            spreadsheet = str(conf.get("spreadsheet_id", ""))
            if not re.fullmatch(r"[A-Za-z0-9_-]{20,100}", spreadsheet):
                raise ValueError("Invalid spreadsheet ID")
            from urllib.parse import quote
            range_name = quote(str(conf.get("range", "Sheet1!A1"))[:100], safe="")
            url = ("https://sheets.googleapis.com/v4/spreadsheets/" + spreadsheet +
                   "/values/" + range_name + ":append?valueInputOption=RAW")
            rows = conf.get("rows", [])
            if not isinstance(rows, list) or len(rows) > 25 or any(
                not isinstance(row, list) or len(row) > 20 for row in rows
            ):
                raise ValueError("Sheets rows must be a small 2D array")
            return self.call("POST", url, token_env=str(conf.get("credential", "")),
                             payload={"values": rows}, allowed={"sheets.googleapis.com"})
        if kind == "facebook_page":
            if conf.get("action") != "publish":
                raise ValueError("Supported Page action: publish")
            page_id = str(conf.get("page_id", ""))
            if not page_id.isdecimal() or len(page_id) > 40:
                raise ValueError("Invalid Facebook page ID")
            message = str(conf.get("message", ""))
            if not message or len(message) > 4000:
                raise ValueError("Invalid Facebook message")
            return self.call("POST", f"https://graph.facebook.com/v27.0/{page_id}/feed",
                             token_env=str(conf.get("credential", "")),
                             payload={"message": message}, allowed={"graph.facebook.com"})
        if kind == "instagram":
            if conf.get("action") != "publish_image":
                raise ValueError("Supported Instagram action: publish_image")
            account = str(conf.get("account_id", ""))
            image_url = str(conf.get("image_url", ""))
            if not account.isdecimal() or len(account) > 40 or not image_url.startswith("https://"):
                raise ValueError("Invalid Instagram account or HTTPS media URL")
            token_env = str(conf.get("credential", ""))
            response = self.call("POST", f"https://graph.facebook.com/v27.0/{account}/media",
                                 token_env=token_env,
                                 payload={"image_url": image_url, "caption": str(conf.get("caption", ""))[:2200]},
                                 allowed={"graph.facebook.com"})
            if not self.live:
                return {**response, "sequence": "create media then publish"}
            creation_id = str(response.get("data", {}).get("id", ""))
            if not creation_id.isdecimal():
                raise ValueError("Instagram media container ID absent")
            return self.call("POST", f"https://graph.facebook.com/v27.0/{account}/media_publish",
                             token_env=token_env, payload={"creation_id": creation_id},
                             allowed={"graph.facebook.com"})
        raise ValueError("Unknown connector")


def execute(workflow: WorkflowDefinition, input_data: dict[str, Any] | None = None,
            *, live: bool = False, approval: bool = False) -> RunResult:
    """Deterministic bounded interpreter with per-node explainable trace."""
    variables = bounded(dict(input_data or {}))
    if any(not IDENT.fullmatch(k) for k in variables):
        raise ValueError("Input variable keys must be identifiers")
    nodes = {n.id: n for n in workflow.nodes}
    current = workflow.start
    trace: list[dict[str, Any]] = []
    connectors = ConnectorExecutor(live=live)
    for step in range(MAX_STEPS):
        node = nodes[current]
        item = {"step": step + 1, "node": node.id, "kind": node.kind}
        try:
            if node.kind == "trigger":
                current = node.next
            elif node.kind == "set":
                name = node.config["variable"]
                variables[name] = bounded(substitute(node.config.get("value", ""), variables))
                current = node.next
            elif node.kind == "transform":
                name = node.config["variable"]
                operation = node.config.get("operation")
                current_value = variables.get(name, "")
                if operation == "uppercase":
                    variables[name] = str(current_value).upper()[:4000]
                elif operation == "lowercase":
                    variables[name] = str(current_value).lower()[:4000]
                elif operation == "strip":
                    variables[name] = str(current_value).strip()[:4000]
                else:
                    raise ValueError("Transform operation not supported")
                current = node.next
            elif node.kind == "condition":
                actual = variables.get(node.config["variable"])
                expected = substitute(node.config.get("value", ""), variables)
                passed = compare(actual, node.config.get("operator", "equals"), expected)
                item["outcome"] = "true" if passed else "false"
                current = node.true_target if passed else node.false_target
            elif node.kind == "approval":
                trace.append({**item, "outcome": "awaiting_approval"})
                if not approval:
                    return RunResult("awaiting_approval", trace, variables, len(trace))
                current = node.next
            elif node.kind == "end":
                trace.append({**item, "outcome": "completed"})
                return RunResult("completed", trace, variables, len(trace))
            elif node.kind in {"http", "google_docs", "google_sheets", "facebook_page", "instagram"}:
                result = connectors.perform(node, variables)
                output_name = node.config.get("save_as", "")
                if output_name:
                    if not isinstance(output_name, str) or not IDENT.fullmatch(output_name):
                        raise ValueError("Invalid output variable")
                    variables[output_name] = bounded(result)
                item["outcome"] = result.get("mode", "executed")
                item["http_status"] = result.get("status")
                current = node.next
            else:
                raise ValueError("Unsupported node")
            bounded(variables)
            trace.append(item)
        except (ValueError, TypeError, KeyError, httpx.HTTPError) as exc:
            # Never log raw secrets, arbitrary HTTP bodies, or user inputs.
            trace.append({**item, "outcome": "failed",
                          "error": str(exc)[:150] if isinstance(exc, ValueError) else "Invalid configuration"})
            return RunResult("failed", trace, {}, len(trace))
    trace.append({"outcome": "limit", "error": "Maximum 50 steps reached"})
    return RunResult("step_limit", trace, variables, MAX_STEPS)
