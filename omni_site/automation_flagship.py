"""Public Automation Flagship: truthful connector catalogue and executable demos.

The public preview only executes server-owned immutable templates in dry-run mode.
No user-defined graph, credentials, or network requests are accepted.
"""

from dataclasses import dataclass

from automation.engine import WorkflowDefinition, execute


@dataclass(frozen=True)
class Integration:
    slug: str
    title: str
    category: str
    capability: str
    status: str
    detail: str


INTEGRATIONS = (
    Integration("http", "HTTPS API", "API", "GET / POST", "gated_live",
                "Публичные HTTPS-хосты из операторского allowlist; для live нужен egress proxy."),
    Integration("google-sheets", "Google Sheets", "Данные", "Добавление строк", "gated_live",
                "Нужны операторские credentials и подтверждённые права к таблице."),
    Integration("google-docs", "Google Docs", "Документы", "Создание документа", "gated_live",
                "Создание через API при настроенных credentials и разрешениях."),
    Integration("facebook-page", "Facebook Pages", "Маркетинг", "Публикация поста", "gated_live",
                "Требуется токен с разрешениями страницы и явное включение live."),
    Integration("instagram", "Instagram", "Маркетинг", "Публикация изображения", "gated_live",
                "Зависит от доступности Graph API и разрешений аккаунта."),
    Integration("webhook", "Incoming Webhook", "Триггеры", "Token-protected dry-run", "dry_run",
                "Публичный webhook выполняется только в режиме симуляции."),
    Integration("telegram", "Telegram", "Мессенджеры", "Проектная интеграция", "separate",
                "Telegram есть в других модулях платформы, но не является узлом этого движка."),
    Integration("payments", "Платёжные провайдеры", "Финансы", "Планирование", "planned",
                "Платёжные действия не доступны как узлы Automation Engine."),
)

STATUS_LABELS = {
    "gated_live": "Live с настройкой и подтверждением",
    "dry_run": "Только dry-run",
    "separate": "В другом модуле",
    "planned": "Не реализовано в движке",
}


@dataclass(frozen=True)
class AutomationTemplate:
    slug: str
    title: str
    audience: str
    description: str
    input_data: dict
    definition: dict


TEMPLATES = (
    AutomationTemplate(
        "lead-qualification", "Квалификация обращения", "Продажи / CRM",
        "Входящая заявка → проверка приоритета → маркировка → ручное согласование.",
        {"priority": "high", "source": "website"},
        {
            "name": "Квалификация обращения",
            "start": "incoming",
            "nodes": [
                {"id": "incoming", "kind": "trigger", "next": "priority_check"},
                {"id": "priority_check", "kind": "condition",
                 "config": {"variable": "priority", "operator": "equals", "value": "high"},
                 "true_target": "mark_hot", "false_target": "mark_normal"},
                {"id": "mark_hot", "kind": "set", "next": "review",
                 "config": {"variable": "segment", "value": "priority"}},
                {"id": "mark_normal", "kind": "set", "next": "review",
                 "config": {"variable": "segment", "value": "standard"}},
                {"id": "review", "kind": "approval", "next": "finish"},
                {"id": "finish", "kind": "end"},
            ],
        },
    ),
    AutomationTemplate(
        "document-routing", "Маршрутизация документа", "Операции / Документы",
        "Новый документ → нормализация категории → выбор маршрута → завершение.",
        {"category": "FINANCE"},
        {
            "name": "Маршрутизация документа",
            "start": "incoming",
            "nodes": [
                {"id": "incoming", "kind": "trigger", "next": "normalize"},
                {"id": "normalize", "kind": "transform", "next": "check",
                 "config": {"variable": "category", "operation": "lowercase"}},
                {"id": "check", "kind": "condition",
                 "config": {"variable": "category", "operator": "equals", "value": "finance"},
                 "true_target": "finance", "false_target": "general"},
                {"id": "finance", "kind": "set", "next": "finish",
                 "config": {"variable": "queue", "value": "finance_review"}},
                {"id": "general", "kind": "set", "next": "finish",
                 "config": {"variable": "queue", "value": "general_review"}},
                {"id": "finish", "kind": "end"},
            ],
        },
    ),
    AutomationTemplate(
        "integration-preview", "Проверка API-интеграции", "Интеграции / API",
        "Триггер → пример HTTPS-запроса (строго dry-run) → результат.",
        {"reference": "demo-001"},
        {
            "name": "Проверка API-интеграции",
            "start": "incoming",
            "nodes": [
                {"id": "incoming", "kind": "trigger", "next": "request"},
                {"id": "request", "kind": "http", "next": "finish",
                 "config": {"url": "https://example.com/api/demo", "method": "GET",
                            "save_as": "api_preview"}},
                {"id": "finish", "kind": "end"},
            ],
        },
    ),
)

BY_SLUG = {item.slug: item for item in TEMPLATES}


def template_definition(slug: str) -> WorkflowDefinition:
    return WorkflowDefinition.model_validate(BY_SLUG[slug].definition)


def preview(slug: str) -> dict:
    template = BY_SLUG[slug]
    result = execute(template_definition(slug), template.input_data, live=False)
    return {
        "template": slug, "mode": "dry_run", "status": result.status,
        "steps": result.steps, "trace": result.trace,
        "variables": result.variables,
        "external_calls_executed": False,
    }
