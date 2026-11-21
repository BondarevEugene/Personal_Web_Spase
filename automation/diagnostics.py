"""Static workflow review: explainable heuristics, never an assurance of security."""
from __future__ import annotations

from collections import deque

from automation.engine import WorkflowDefinition

CONNECTORS = {"http", "google_docs", "google_sheets", "facebook_page", "instagram"}
WRITES = {"google_docs", "google_sheets", "facebook_page", "instagram"}


def analyze(workflow: WorkflowDefinition) -> dict:
    by_id = {node.id: node for node in workflow.nodes}
    reached = set()
    queue = deque([workflow.start])
    while queue:
        id = queue.popleft()
        if id in reached:
            continue
        reached.add(id)
        node = by_id[id]
        for target in (node.next, node.true_target, node.false_target):
            if target and target not in reached:
                queue.append(target)
    warnings: list[dict] = []
    suggestions: list[str] = []
    for node in workflow.nodes:
        if node.id not in reached:
            warnings.append({"node": node.id, "type": "unreachable",
                             "message": "Узел недостижим от старта"})
        if node.kind in CONNECTORS and not node.config.get("credential"):
            warnings.append({"node": node.id, "type": "credentials",
                             "message": "Не указана ссылка на секрет оператора"})
        if node.kind == "http":
            if not str(node.config.get("url", "")).startswith("https://"):
                warnings.append({"node": node.id, "type": "destination",
                                 "message": "HTTP-коннектор требует HTTPS"})
        if node.kind in WRITES or (node.kind == "http" and node.config.get("method") == "POST"):
            warnings.append({"node": node.id, "type": "side_effect",
                             "message": "Узел изменяет внешние данные; повторный запуск требует идемпотентности"})
    terminals = [n.id for n in workflow.nodes if n.kind == "end" and n.id in reached]
    if not terminals:
        warnings.append({"node": workflow.start, "type": "no_terminal",
                         "message": "Нет достижимого узла завершения"})
        suggestions.append("Добавь достижимый блок завершения")
    if not any(n.kind == "approval" for n in workflow.nodes) and any(
        n.kind in WRITES for n in workflow.nodes
    ):
        suggestions.append("Перед необратимыми публикациями предусмотрите согласование и отдельный процесс подтверждения")
    if len(reached) < len(workflow.nodes):
        suggestions.append("Удали недостижимые блоки или исправь переходы")
    if not any(n.kind == "condition" for n in workflow.nodes):
        suggestions.append("Если процесс обрабатывает разные категории входных данных, добавь условия")
    if not any(n.kind in CONNECTORS for n in workflow.nodes):
        suggestions.append("Подключи HTTP или внешний сервис только после проверки схемы на dry-run")
    return {"name": workflow.name, "nodes_total": len(workflow.nodes),
            "nodes_reachable": len(reached), "terminal_nodes": terminals,
            "external_connectors": sum(n.kind in CONNECTORS for n in workflow.nodes),
            "warnings": warnings, "recommendations": suggestions,
            "limitations": ("Статическая проверка, а не гарантия безопасности, "
                            "работоспособности OAuth или стоимости внешних API.")}
