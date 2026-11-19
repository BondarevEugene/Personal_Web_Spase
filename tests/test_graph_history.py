"""Graph Studio undo/redo contract and executable history tests.

If Node.js is installed in CI, exercise the pure JavaScript history engine.
If not, structural contracts still protect the HTML/JS integration.
"""
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
JS_FILE = ROOT / "omni_site" / "static" / "graph_history.js"


def test_editor_loads_history_before_graph_studio():
    page = (ROOT / "templates" / "builder_pro_final.html").read_text(
        encoding="utf-8"
    )
    assert page.index("/studio-assets/graph_history.js?v=1") < page.index(
        "/studio-assets/graph_studio.js?v=9"
    )
    for marker in ('id="graph-undo"', 'id="graph-redo"'):
        assert marker in page


def test_editor_restores_all_core_scenario_state_and_respects_form_shortcuts():
    js = (ROOT / "omni_site" / "static" / "graph_studio.js").read_text(
        encoding="utf-8"
    )
    for marker in (
        "function graphState()", "function undoGraph()", "function redoGraph()",
        "snapshot.data", "snapshot.positions", "resetHistory()",
        "graphHistory.record", "target.isContentEditable",
        "target.matches('input,textarea,select')", "restoreGraph(graphHistory.undo())",
    ):
        assert marker in js, marker
    assert "historyTypingGroup=typingGroup" in js
    assert "graphHistory.reset(graphState())" in js


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_history_engine_undo_redo_snapshots_and_branches():
    script = r"""
const assert = require('node:assert/strict');
const history = require(process.argv[1]);
const first = {data:{name:'bot',start:'a',nodes:[{id:'a',next:null}]},positions:{a:{x:1,y:2}}};
const h = history.create(first,3);
assert.equal(h.canUndo(),false);
let second = JSON.parse(JSON.stringify(first));
second.data.nodes[0].next='b';
second.data.nodes.push({id:'b',next:null});
second.positions.b={x:20,y:30};
h.record(second);
second.positions.b.x=999;
assert.equal(h.undo().positions.a.x,1);
assert.equal(h.redo().positions.b.x,20);
assert.equal(h.canRedo(),false);
h.undo();
const fork=JSON.parse(JSON.stringify(first));
fork.data.name='new name';
h.record(fork);
assert.equal(h.canRedo(),false);
assert.equal(h.undo().data.name,'bot');
h.reset(fork);
assert.equal(h.canUndo(),false);
assert.equal(h.canRedo(),false);
const v1=JSON.parse(JSON.stringify(fork));
v1.data.name='N';
const v2=JSON.parse(JSON.stringify(fork));
v2.data.name='New';
h.record(v1,'field:1');
h.record(v2,'field:1');
assert.equal(h.length(),2);
assert.equal(h.undo().data.name,'new name');
console.log('Graph history OK');
"""
    result = subprocess.run(
        [shutil.which("node"), "-e", script, str(JS_FILE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Graph history OK" in result.stdout
