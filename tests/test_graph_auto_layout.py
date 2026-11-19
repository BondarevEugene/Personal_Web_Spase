"""Graph Studio auto-layout: executable graph rules and persistence contracts."""
from pathlib import Path
import shutil
import subprocess

import pytest
from pydantic import ValidationError

from api.builder_projects import Coordinates


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "omni_site" / "static" / "graph_layout.js"


def test_auto_layout_controls_and_editor_wiring():
    html = (ROOT / "templates" / "builder_pro_final.html").read_text(
        encoding="utf-8"
    )
    js = (ROOT / "omni_site" / "static" / "graph_studio.js").read_text(
        encoding="utf-8"
    )
    assert html.index("graph_history.js?v=1") < html.index(
        "graph_layout.js?v=1"
    ) < html.index("graph_studio.js?v=10")
    assert 'id="btn-auto-layout"' in html
    assert "window.OmniGraphLayout.arrange(payload())" in js
    assert "positions=layout.positions;" in js
    assert "change();inspector();" in js
    assert "function undoGraph()" in js


def test_taller_layout_coordinates_are_accepted_but_bounded():
    assert Coordinates(x=1800, y=3500).y == 3500
    with pytest.raises(ValidationError):
        Coordinates(x=2201, y=3500)
    with pytest.raises(ValidationError):
        Coordinates(x=1800, y=8001)


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js not installed")
def test_auto_layout_determinism_cycles_disconnected_and_80_nodes():
    code = r"""
const assert = require('node:assert/strict');
const {arrange} = require(process.argv[1]);
const graph = {
 name:'Branch',start:'start',
 nodes:[
  {id:'start',kind:'message',next:'choose'},
  {id:'choose',kind:'choice',options:[{target:'left'},{target:'right'}]},
  {id:'left',kind:'message',next:'start'},
  {id:'right',kind:'end'},
  {id:'orphan',kind:'message'}
 ]
};
const original=JSON.stringify(graph);
const a=arrange(graph);
const b=arrange(graph);
assert.deepEqual(a,b);
assert.equal(JSON.stringify(graph),original);
assert.equal(a.nodes,5);
assert.equal(a.disconnected,1);
assert(a.positions.left.x>a.positions.choose.x);
assert(a.positions.right.x>a.positions.choose.x);
assert.equal(new Set(Object.values(a.positions).map(p=>p.x+','+p.y)).size,5);
const big={name:'80 nodes',start:'n0',nodes:Array.from({length:80},(_,i)=>({
 id:'n'+i,kind:i===79?'end':'message',next:i===79?null:'n'+(i+1)
}))};
const c=arrange(big);
assert.equal(c.mode,'wrapped');
assert.equal(c.nodes,80);
assert(c.height>1400 && c.height<=8000);
assert.equal(new Set(Object.values(c.positions).map(p=>p.x+','+p.y)).size,80);
assert(Object.values(c.positions).every(p=>p.x>=0&&p.x<=2200&&p.y>=0&&p.y<=8000));
console.log('auto layout OK');
"""
    result = subprocess.run(
        [shutil.which("node"), "-e", code, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "auto layout OK" in result.stdout
