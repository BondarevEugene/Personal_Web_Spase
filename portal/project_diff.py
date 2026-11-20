"""Safe, bounded textual comparison of immutable project document versions."""
from __future__ import annotations

from difflib import SequenceMatcher

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from portal.client_projects import customer_project, project_key
from portal.db import session_factory
from portal.models import ClientProjectDocument
from portal.routes import current_customer
from portal.security import secure_request

router = APIRouter(prefix="/account/projects", tags=["Project document comparison"])

MAX_LINES = 1200


def compare_text(previous: str, current: str) -> list[dict[str, str]]:
    """Line-by-line diff with explicit escaping deferred to Jinja autoescape."""
    before = previous.splitlines()[:MAX_LINES]
    after = current.splitlines()[:MAX_LINES]
    matcher = SequenceMatcher(None, before, after, autojunk=False)
    output = []
    for tag, a1, a2, b1, b2 in matcher.get_opcodes():
        if tag in {"equal", "replace", "delete"}:
            output.extend({"kind": "removed" if tag != "equal" else "same",
                           "text": line} for line in before[a1:a2])
        if tag in {"replace", "insert"}:
            output.extend({"kind": "added", "text": line} for line in after[b1:b2])
    return output


@router.get("/{id}/documents/{document_id}/compare", response_class=HTMLResponse)
def compare_document(request: Request, id: str, document_id: str):
    secure_request(request)
    with session_factory()() as db:
        user = current_customer(request, db)
        if user is None:
            raise HTTPException(401, "Войдите в кабинет")
        project = customer_project(db, user, id)
        current = db.scalar(select(ClientProjectDocument).where(
            ClientProjectDocument.id == project_key(document_id),
            ClientProjectDocument.project_id == project.id,
        ))
        if current is None:
            raise HTTPException(404, "Документ не найден")
        if current.version <= 1:
            raise HTTPException(409, "Для первой версии сравнение недоступно")
        previous = db.scalar(select(ClientProjectDocument).where(
            ClientProjectDocument.project_id == project.id,
            ClientProjectDocument.document_kind == current.document_kind,
            ClientProjectDocument.version == current.version - 1,
        ))
        if previous is None:
            raise HTTPException(409, "Предыдущая редакция не найдена")
        from html import escape

        lines = compare_text(previous.body, current.body)
        parts = [
            '<!doctype html><html lang="ru"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            '<meta name="robots" content="noindex,nofollow">',
            '<title>Сравнение редакций — OMNIFACTORY</title>',
            '<style>body{font:16px system-ui;max-width:1100px;margin:auto;'
            'padding:2rem;background:#101827;color:#f0f5ff}'
            'a{color:#a9d6ff}.diff{font:13px/1.6 ui-monospace,monospace;'
            'white-space:pre-wrap;overflow-wrap:anywhere;border-radius:8px;'
            'padding:3px 12px}.added{background:#163b32}'
            '.removed{background:#48252d}.same{opacity:.7}'
            '</style></head><body>',
            f'<a href="/account/projects/{escape(project.id)}">← К проекту</a>',
            '<h1>Сравнение редакций документа</h1>',
            f'<p>{escape(current.title)}: v{previous.version} → v{current.version}</p>',
            '<p>Зелёный — добавлено, красный — удалено.</p>',
        ]
        for line in lines:
            parts.append(
                f'<div class="diff {line["kind"]}">'
                f'{escape(line["text"]) or " "}</div>'
            )
        parts.append("</body></html>")
        return HTMLResponse(
            "".join(parts),
            headers={"Cache-Control": "no-store",
                     "X-Robots-Tag": "noindex, nofollow",
                     "X-Content-Type-Options": "nosniff"},
        )
