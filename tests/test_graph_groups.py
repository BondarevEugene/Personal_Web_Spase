"""Logical groups are saved annotations, not executable graph nodes."""
from pathlib import Path
import shutil
import subprocess

import pytest
from pydantic import ValidationError

from api.builder_projects import ProjectData, pack_layout, unpack_layout

ROOT = Path(__file__).resolve().parents[1]
GROUP_SCRIPT = ROOT / "omni_site" / "static" / "graph_groups.js"

SCENARIO = {
    "name": "Grouped bot",
    "start": "welcome",
    "nodes": [
        {"id": "welcome", "kind": "message", "text": "Hello", "next": "finish"},
        {"id": "finish", "kind": "end", "text": "Done"},
    ],
}
GROUP = {"id": "group1", "title": "Первый этап", "node_ids": ["welcome"]}


def test_group_layout_round_trip_and_legacy_positions():
    data = ProjectData.model_validate({
        "scenario": SCENARIO,
        "positions": {"welcome": {"x": 80, "y": 200}},
        "groups": [GROUP],
    })
    positions, groups = unpack_layout(pack_layout(data))
    assert groups == [GROUP]
    assert positions["welcome"] == {"x": 80.0, "y": 200.0}
    old_positions, old_groups = unpack_layout(
        '{"welcome": {"x": 10.0, "y": 20.0}}'
    )
    assert old_positions["welcome"]["x"] == 10.0
    assert old_groups == []


@pytest.mark.parametrize("groups", [
    [{"id": "bad-name", "title": "Two", "node_ids": ["welcome"]}],
    [{"id": "group1", "title": "A", "node_ids": ["welcome"]}],
    [{"id": "group1", "title": "Valid", "node_ids": ["missing"]}],
    [{"id": "group1", "title": "Valid", "node_ids": ["welcome", "welcome"]}],
    [
        {"id": "group1", "title": "First", "node_ids": ["welcome"]},
        {"id": "group1", "title": "Second", "node_ids": ["finish"]},
    ],
    [
        {"id": "group1", "title": "First", "node_ids": ["welcome"]},
        {"id": "group2", "title": "Second", "node_ids": ["welcome"]},
    ],
])
def test_invalid_group_metadata_is_rejected(groups):
    with pytest.raises(ValidationError):
        ProjectData.model_validate({"scenario": SCENARIO, "groups": groups})


def test_group_ui_preserves_export_scenario_contract():
    html = (ROOT / "templates" / "builder_pro_final.html").read_text(
        encoding="utf-8"
    )
    js = (ROOT / "omni_site" / "static" / "graph_studio.js").read_text(
        encoding="utf-8"
    )
    assert html.index("graph_groups.js?v=1") < html.index("graph_studio.js?v=12")
    for control in ("graph-group-create", "graph-group-apply", "graph-groups-list",
                    "graph-group-target", "graph-group-name"):
        assert f'id="{control}"' in html
    assert "window.OmniGraphGroups.create" in js
    assert "window.OmniGraphGroups.move" in js
    assert "window.OmniGraphGroups.ungroup" in js
    assert "graphState(){return {data,positions,groups};}" in js
    assert "body:JSON.stringify({scenario:payload(),positions,groups})" in js
    # Only graph nodes, never group objects, are sent to Python export/simulator.
    assert "function payload(){return {name:data.name,start:data.start,nodes:" in js


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_group_membership_operations_and_non_destructive_deletion():
    js = r"""
const assert = require('node:assert/strict');
const api = require(process.argv[1]);
const nodes=[{id:'a',next:'b'},{id:'b',next:null},{id:'c',next:null}];
const before=JSON.stringify(nodes);
let groups=api.create([],nodes,'Welcome','a');
assert.equal(groups.length,1);
groups=api.move(groups,nodes,'group1','b');
assert.deepEqual(groups[0].node_ids,['a','b']);
groups=api.create(groups,nodes,'Other','c');
groups=api.move(groups,nodes,'group2','b');
assert.deepEqual(groups[0].node_ids,['a']);
assert.deepEqual(groups[1].node_ids,['c','b']);
groups=api.ungroup(groups,'a');
assert.equal(groups.length,1);
assert.deepEqual(groups[0].node_ids,['c','b']);
groups=api.deleteGroup(groups,'group2');
assert.deepEqual(groups,[]);
assert.equal(JSON.stringify(nodes),before);
console.log('group metadata OK');
"""
    result = subprocess.run(
        [shutil.which("node"), "-e", js, str(GROUP_SCRIPT)],
        cwd=ROOT, capture_output=True, text=True, check=False, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "group metadata OK" in result.stdout
