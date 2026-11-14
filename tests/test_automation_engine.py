"""Network-free execution and security tests for the Automation Engine."""
import pytest
from pydantic import ValidationError

from automation.engine import (
    WorkflowDefinition, bounded, compare, execute, public_host, substitute,
)

DEMO = {
    "name": "Explainable lead routing",
    "start": "trigger",
    "nodes": [
        {"id": "trigger", "kind": "trigger", "next": "setname"},
        {"id": "setname", "kind": "set", "next": "clean",
         "config": {"variable": "name", "value": "{{lead}}"}},
        {"id": "clean", "kind": "transform", "next": "qualify",
         "config": {"variable": "name", "operation": "strip"}},
        {"id": "qualify", "kind": "condition", "true_target": "yes",
         "false_target": "no", "config": {
             "variable": "name", "operator": "equals", "value": "Alice"}},
        {"id": "yes", "kind": "end"},
        {"id": "no", "kind": "end"},
    ],
}


def test_engine_explains_both_routes_without_external_calls():
    workflow = WorkflowDefinition.model_validate(DEMO)
    yes = execute(workflow, {"lead": " Alice "})
    no = execute(workflow, {"lead": "Bob"})
    assert yes.status == no.status == "completed"
    assert [x["node"] for x in yes.trace] == ["trigger", "setname", "clean", "qualify", "yes"]
    assert [x["node"] for x in no.trace] == ["trigger", "setname", "clean", "qualify", "no"]
    assert yes.trace[3]["outcome"] == "true"
    assert no.trace[3]["outcome"] == "false"
    assert yes.variables["name"] == "Alice"


def test_validation_rejects_unknown_target_and_missing_branch():
    payload = {**DEMO, "nodes": [dict(n) for n in DEMO["nodes"]]}
    payload["nodes"][3]["false_target"] = "unknown"
    with pytest.raises(ValidationError):
        WorkflowDefinition.model_validate(payload)
    payload["nodes"][3]["false_target"] = None
    with pytest.raises(ValidationError):
        WorkflowDefinition.model_validate(payload)


def test_cycles_stay_bounded():
    flow = WorkflowDefinition.model_validate({
        "name": "Bounded loop", "start": "a",
        "nodes": [{"id": "a", "kind": "set", "next": "a",
                   "config": {"variable": "x", "value": "ok"}}],
    })
    result = execute(flow, {})
    assert result.status == "step_limit"
    assert result.steps == 50


def test_approval_always_pauses_and_does_not_execute_successor():
    flow = WorkflowDefinition.model_validate({
        "name": "Approval", "start": "review",
        "nodes": [{"id": "review", "kind": "approval", "next": "done"},
                  {"id": "done", "kind": "end"}],
    })
    assert execute(flow).status == "awaiting_approval"


def test_http_connector_dry_run_never_uses_network(monkeypatch):
    monkeypatch.setenv("OMNI_AUTOMATION_ALLOWED_HOSTS", "example.com")
    def fail(*args, **kwargs):
        raise AssertionError("An HTTP request was attempted")
    monkeypatch.setattr("automation.engine.httpx.Client", fail)
    flow = WorkflowDefinition.model_validate({
        "name": "Call HTTP", "start": "trigger",
        "nodes": [
            {"id": "trigger", "kind": "trigger", "next": "send"},
            {"id": "send", "kind": "http", "next": "done",
             "config": {"url": "https://example.com/path", "method": "POST",
                        "body": {"name": "{{name}}"}, "save_as": "result"}},
            {"id": "done", "kind": "end"},
        ],
    })
    result = execute(flow, {"name": "Alice"})
    assert result.status == "completed"
    assert result.trace[1]["outcome"] == "dry_run"
    assert result.variables["result"]["mode"] == "dry_run"


@pytest.mark.parametrize("url", [
    "http://example.com/", "https://127.0.0.1/", "https://localhost/",
    "https://someone:secret@example.com/", "https://example.com:8443/",
    "https://example.com/#private", "https://evil.com/",
])
def test_destination_policy_rejects_unapproved_addresses(url):
    with pytest.raises(ValueError):
        public_host(url, {"example.com"})


def test_variable_template_is_plain_substitution_not_eval():
    assert substitute("Hello {{name}}", {"name": "Alice"}) == "Hello Alice"
    assert substitute("{{__import__('os')}}", {}) == "{{__import__('os')}}"
    assert compare("100", "greater", "30")
    assert not compare("foo", "greater", "30")
    with pytest.raises(ValueError):
        bounded({"oversized": "x" * 100000})


def test_no_arbitrary_python_execution_supported():
    with pytest.raises(ValidationError):
        WorkflowDefinition.model_validate({
            "name": "Dangerous", "start": "p",
            "nodes": [{"id": "p", "kind": "python",
                       "config": {"code": "import os"}}],
        })
