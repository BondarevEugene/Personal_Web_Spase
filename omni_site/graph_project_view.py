"""Customer-scoped, read-only Graph Studio project overview."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from api.builder_projects import customer_required, project_id, serialize
from portal.db import session_factory
from portal.models import BuilderProject

router = APIRouter(tags=["Graph Studio project overview"])


@router.get("/account/graph-project/{id}", response_class=HTMLResponse)
def open_graph_project(request: Request, id: str):
    """Render only the authenticated customer's own saved graph."""
    from html import escape

    with session_factory()() as db:
        customer = customer_required(request, db)
        row = db.scalar(
            select(BuilderProject).where(
                BuilderProject.id == project_id(id),
                BuilderProject.customer_id == customer.id,
            )
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Project not found")
        project = serialize(row, full=True)
    nodes = project["scenario"]["nodes"]
    title = escape(project["name"])
    items = "".join(
        "<li><strong>" + escape(node["id"]) + "</strong> · "
        + escape(node["kind"]) + " — "
        + escape(node.get("text") or node.get("media") or "")
        + "</li>"
        for node in nodes
    )
    html = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>' + title + ' · OMNIFACTORY</title>'
        '<style>body{font:16px system-ui;background:#090e19;color:#eef3ff;'
        'max-width:900px;margin:auto;padding:clamp(20px,5vw,64px)}'
        'a{color:#c3b3ff}li{padding:15px;margin:12px 0;'
        'background:#182237;border:1px solid #394862;border-radius:12px}'
        'h1{font-size:clamp(28px,5vw,52px)}'
        '#graph-canvas{position:relative;overflow:auto;min-height:440px;'
        'border:1px solid #455676;border-radius:14px;'
        'background:linear-gradient(#17233b55 1px,transparent 1px),'
        'linear-gradient(90deg,#17233b55 1px,transparent 1px),#0c1424;'
        'background-size:24px 24px;margin:20px 0}'
        '.graph-node{position:absolute;width:190px;box-sizing:border-box;'
        'padding:14px;background:#243552;border:1px solid #7184b0;'
        'border-radius:12px;cursor:grab;touch-action:none;user-select:none}'
        '.graph-node:focus{outline:3px solid #c3b3ff}'
        '#graph-canvas svg{position:absolute;inset:0;pointer-events:none}'
        '#graph-toolbar button,#graph-save{padding:10px 16px;margin:6px;'
        'background:#c3b3ff;color:#101526;border:0;border-radius:8px;cursor:pointer}'
        '</style></head><body>'
        '<nav><a href="/account">← Личный кабинет</a> · '
        '<a href="/builder-pro">Graph Studio</a></nav>'
        '<h1>' + title + '</h1><p>Сохранённый сценарий · '
        + str(len(nodes)) + ' блоков</p><ol>' + items + '</ol>'
        '<p>Для изменения узлов откройте Graph Studio. '
        'Это защищённый просмотр, а не режим редактирования.</p>'
        '<section id="graph-editor" data-project-id="' + escape(project["id"]) + '">'
        '<h2>Редактор сценария</h2><p>Изменяйте тексты, названия и переходы блоков. '
        'Проверка графа выполняется сервером перед сохранением.</p>'
        '<div id="graph-toolbar"><button type="button" id="graph-add-message">+ Сообщение</button> '
        '<button type="button" id="graph-add-end">+ Завершение</button></div>'
        '<div id="graph-canvas" aria-label="Визуальная схема сценария"></div>'
        '<div id="graph-editor-fields"></div>'
        '<button type="button" id="graph-save">Сохранить изменения</button>'
        '<p id="graph-editor-status" role="status" aria-live="polite"></p>'
        '</section><script defer src="/studio-assets/graph_project_editor.js"></script>'
        '</body></html>'
    )
    return HTMLResponse(
        html, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"}
    )
