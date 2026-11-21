"""Deployment plans must be created for a saved revision and visibly become stale."""
from pathlib import Path

from test_builder_projects import BASE, SCENARIO, csrf, db_ready, register


def test_plan_requires_revision_and_tracks_current_vs_stale(db_ready):
    owner = register("plan_owner", "plan-owner@builder.test")
    outsider = register("plan_outsider", "plan-outsider@builder.test")
    created = owner.post(BASE, headers=csrf(owner), json={"scenario": SCENARIO})
    assert created.status_code == 201, created.text
    project_id = created.json()["id"]
    revision = created.json()["revision"]
    endpoint = BASE + "/" + project_id + "/deployment-plan"
    readiness = BASE + "/" + project_id + "/deployment-readiness"
    payload = {
        "name": "my-telegram-bot",
        "mode": "managed",
        "transport": "worker",
        "max_monthly_usd": 20,
    }
    assert outsider.get(readiness).status_code == 404
    assert outsider.post(endpoint, headers=csrf(outsider),
                         json={**payload, "revision": revision}).status_code == 404
    assert owner.post(endpoint, headers=csrf(owner), json=payload).status_code == 422
    assert owner.post(endpoint, json={**payload, "revision": revision}).status_code == 403
    assert owner.post(endpoint, headers=csrf(owner),
                      json={**payload, "revision": "0" * 64}).status_code == 409

    first = owner.post(endpoint, headers=csrf(owner),
                       json={**payload, "revision": revision})
    assert first.status_code == 201, first.text
    assert first.json()["status"] == "planned"
    repeated = owner.post(endpoint, headers=csrf(owner),
                          json={**payload, "revision": revision})
    assert repeated.status_code == 201
    assert repeated.json()["already_exists"] is True
    assert repeated.json()["id"] == first.json()["id"]
    status = owner.get(readiness)
    assert status.status_code == 200
    assert status.json()["revision"] == revision
    assert status.json()["saved_plans"][0]["current_revision"] is True
    assert status.json()["saved_plans"][0]["provider"] == "railway"
    assert status.json()["live_deployment_enabled"] is False

    changed = owner.put(
        BASE + "/" + project_id,
        headers={**csrf(owner), "If-Match": revision},
        json={"scenario": {**SCENARIO, "name": "Edited bot"}},
    )
    assert changed.status_code == 200, changed.text
    new_revision = changed.json()["revision"]
    assert new_revision != revision
    after = owner.get(readiness).json()
    assert after["revision"] == new_revision
    assert after["saved_plans"][0]["current_revision"] is False
    assert owner.post(endpoint, headers=csrf(owner),
                      json={**payload, "revision": revision}).status_code == 409
    next_plan = owner.post(endpoint, headers=csrf(owner),
                           json={**payload, "revision": new_revision})
    assert next_plan.status_code == 201, next_plan.text
    assert next_plan.json()["id"] != first.json()["id"]
    latest = owner.get(readiness).json()
    assert sum(plan["current_revision"] for plan in latest["saved_plans"]) == 1


def test_editor_passes_revision_and_blocks_dirty_deployment():
    source = (Path(__file__).resolve().parents[1] /
              "omni_site/static/graph_project_editor.js").read_text(encoding="utf-8")
    assert "revision: project.revision" in source
    assert 'if (dirty) {' in source
    assert 'data.revision !== project.revision' in source
    assert "plan.current_revision" in source
