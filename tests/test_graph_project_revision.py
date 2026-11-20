"""Graph Studio revision and backup contract tests."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.builder_projects import ensure_revision, project_revision


def test_revision_changes_for_scenario_or_layout():
    row = SimpleNamespace(scenario_json='{"nodes":[]}', layout_json="{}")
    original = project_revision(row)
    assert len(original) == 64
    row.layout_json = '{"positions":{"n1":{"x":10,"y":20}}}'
    assert project_revision(row) != original
    row.layout_json = "{}"
    row.scenario_json = '{"nodes":[{"id":"n1"}]}'
    assert project_revision(row) != original


def test_if_match_rejects_stale_editor_without_mutating():
    row = SimpleNamespace(scenario_json="{}", layout_json="{}")
    request = SimpleNamespace(headers={"If-Match": "stale"})
    with pytest.raises(HTTPException) as exc:
        ensure_revision(request, row)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "PROJECT_CHANGED"
    assert exc.value.detail["current_revision"] == project_revision(row)


def test_current_revision_is_accepted():
    row = SimpleNamespace(scenario_json="{}", layout_json="{}")
    request = SimpleNamespace(headers={"If-Match": project_revision(row)})
    ensure_revision(request, row)
