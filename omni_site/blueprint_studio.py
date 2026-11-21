"""OMNIFACTORY Blueprint Studio — deterministic, non-persistent scoping.

Only curated business options are accepted. The blueprint is guidance, not a
price quotation, confirmed implementation or deployable architecture.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

from omni_site.solution_journeys import BY_SLUG


@dataclass(frozen=True)
class Option:
    key: str
    title: str
    detail: str


@dataclass(frozen=True)
class Blueprint:
    sector: str
    title: str
    objective: str
    team: Option
    process: Option
    priority: Option
    integrations: tuple[Option, ...]
    components: tuple[str, ...]
    stages: tuple[str, ...]
    acceptance: tuple[str, ...]
    risks: tuple[str, ...]
    next_questions: tuple[str, ...]
    lead_url: str
    text: str


SECTORS = (
    Option("crm", "CRM и клиентские процессы", "Заявки, статусы, документы, согласование"),
    Option("telegram", "Telegram и цифровые продукты", "Диалог, материалы, выдача результата"),
    Option("automation", "Автоматизация процессов", "События, правила, интеграции, контроль"),
    Option("ai", "AI-ассистенты и интеллектуальные системы", "Контекст, качество, проверка человеком"),
)
TEAMS = (
    Option("solo", "1–5 человек", "Маленькая команда и простое распределение ролей"),
    Option("growth", "6–30 человек", "Несколько ролей и ответственных"),
    Option("enterprise", "31+ человек", "Разделение доступов и сложные согласования"),
)
PROCESSES = (
    Option("new", "Запуск с нуля", "Первый прототип и описание бизнес-процесса"),
    Option("manual", "Ручная работа", "Заменить повторяющиеся действия и таблицы"),
    Option("legacy", "Есть действующая система", "Поэтапная интеграция без потери данных"),
)
PRIORITIES = (
    Option("speed", "Сократить ручные операции", "Убрать повторяющиеся шаги"),
    Option("control", "Прозрачность и контроль", "Статусы, история действий, контроль ошибок"),
    Option("experience", "Улучшить клиентский опыт", "Снизить число действий и ошибок пользователей"),
)
INTEGRATIONS = (
    Option("telegram", "Telegram", "Сообщения, уведомления, сценарии"),
    Option("database", "PostgreSQL / Neon", "Структурированное хранение и миграции"),
    Option("payments", "Оплата", "Платёжный шлюз и серверное подтверждение"),
    Option("external", "Сторонний API", "Интеграция по подтверждённому интерфейсу"),
)

SECTOR_BY_KEY = {item.key: item for item in SECTORS}
TEAM_BY_KEY = {item.key: item for item in TEAMS}
PROCESS_BY_KEY = {item.key: item for item in PROCESSES}
PRIORITY_BY_KEY = {item.key: item for item in PRIORITIES}
INTEGRATION_BY_KEY = {item.key: item for item in INTEGRATIONS}

BASE_COMPONENTS = {
    "crm": (
        "FastAPI: маршруты клиентов, проектов и задач",
        "SQLAlchemy / Alembic: модели и миграции",
        "Jinja2: адаптивный кабинет и состояния проекта",
        "Серверная авторизация и изоляция организаций",
    ),
    "telegram": (
        "aiogram: состояния, команды и навигация бота",
        "Сервисная обработка входных материалов",
        "Python-воркфлоу подготовки и выдачи результата",
        "Хранение заказов и контроль повторных запросов",
    ),
    "ai": (
        "FastAPI: проверяемый API-контур для AI-сценариев",
        "Адаптер модели, контроль токенов, затрат и таймаутов",
        "Разрешённые источники контекста и проверка доступа",
        "Ручное подтверждение критичных ответов и журнал качества",
    ),
    "automation": (
        "Модель событий, условий и шагов workflow",
        "Исполнитель задач с ограничениями и журналом ошибок",
        "Валидация данных и безопасная обработка исключений",
        "Режим тестирования сценария до боевой интеграции",
    ),
}
BASE_STAGES = (
    "Аудит текущего процесса и проверка источников данных",
    "Карта пользовательских маршрутов, роли и границы MVP",
    "Прототип и согласование критериев приёмки",
    "Разработка, миграции, тесты и проверка интеграций",
    "Пилот, документация, передача и план развития",
)
BASE_ACCEPTANCE = {
    "crm": (
        "Операции доступны только разрешённым ролям и организациям",
        "Смена этапов и версий документов воспроизводима",
        "Ошибки валидации не нарушают сохранность заказов",
    ),
    "telegram": (
        "Пользователь проходит маршрут без пропуска обязательных шагов",
        "Повторный запрос не создаёт нежелательную повторную выдачу",
        "Ошибки генерации корректно отображаются и протоколируются",
    ),
    "ai": (
        "Набор контрольных запросов проверяет качество и типовые ошибки",
        "Недоступность модели не приводит к потере данных и повторным действиям",
        "Критичные решения не выполняются без подтверждения оператора",
    ),
    "automation": (
        "Условия и переменные проверяются на тестовых примерах",
        "Сбой стороннего API не приводит к бесконечному повторению",
        "Оператор видит результат, ошибки и действия для восстановления",
    ),
}
SECTOR_QUESTIONS = {
    "crm": "Какие документы и роли должны участвовать в согласовании?",
    "telegram": "Какие исходные файлы, действия клиента и форматы результата обязательны?",
    "automation": "Какие события запускают процесс и какие API доступны официально?",
    "ai": "Какие источники данных разрешены, как проверяем точность и кто утверждает ответы?",
}
LEAD_TOPIC = {
    "crm": "CRM / управление бизнесом",
    "telegram": "Telegram Bot / Mini App",
    "automation": "AI / автоматизация",
    "ai": "AI / автоматизация",
}


def _select(key: str, catalog: dict[str, Option], field: str) -> Option:
    selected = catalog.get(key)
    if selected is None:
        raise ValueError(f"Недопустимое значение параметра: {field}")
    return selected


def make_blueprint(
    sector: str,
    team: str,
    process: str,
    priority: str,
    integrations: tuple[str, ...] = (),
) -> Blueprint:
    """Return a bounded first-pass specification without storing inputs."""
    choice = _select(sector, SECTOR_BY_KEY, "направление")
    team_option = _select(team, TEAM_BY_KEY, "масштаб команды")
    process_option = _select(process, PROCESS_BY_KEY, "стадия процесса")
    priority_option = _select(priority, PRIORITY_BY_KEY, "приоритет")
    if len(integrations) > 4 or len(set(integrations)) != len(integrations):
        raise ValueError("Повторяющиеся или избыточные интеграции")
    selected = tuple(
        _select(item, INTEGRATION_BY_KEY, "интеграция")
        for item in integrations
    )
    if process == "legacy":
        migration = ("Ревизия существующей схемы данных и безопасный план переноса",)
    else:
        migration = ("Описание исходных данных и правил их проверки",)
    extra = []
    if team == "enterprise":
        extra.append("Матрица ролей, аудит доступа и журнал изменений")
    if "payments" in integrations:
        extra.append("Серверная верификация оплаты и идемпотентность callback")
    if "external" in integrations:
        extra.append("API-контракт, таймауты, ретраи и отдельный sandbox")
    if priority == "control":
        extra.append("Журнал аудита, наблюдаемость и понятные статусы операций")
    components = BASE_COMPONENTS[sector] + tuple(extra)
    stages = BASE_STAGES[:1] + migration + BASE_STAGES[1:]
    acceptance = BASE_ACCEPTANCE[sector] + (
        "Согласованные интеграции проверены на тестовом контуре",
        "Проект имеет инструкцию по запуску, резервированию и восстановлению",
    )
    risks = list(BY_SLUG[sector].constraints)
    if "payments" in integrations:
        risks.append("Доступность и комиссии платёжного провайдера проверяются отдельно")
    if process == "legacy":
        risks.append("Сроки миграции нельзя оценить без изучения текущих данных")
    if team == "enterprise":
        risks.append("Расширенные права и нормативные требования требуют отдельного аудита")
    questions = (
        SECTOR_QUESTIONS[sector],
        "Где сейчас хранятся данные и кто отвечает за поддержку?",
        "Какие действия нужно обязательно оставить на ручное подтверждение?",
    )
    lead_url = "/studio?topic=" + quote(LEAD_TOPIC[sector], safe="") + "#contact"
    lines = [
        "OMNIFACTORY / ПРЕДВАРИТЕЛЬНЫЙ ПРОЕКТНЫЙ БРИФ",
        f"Направление: {choice.title}",
        f"Команда: {team_option.title}",
        f"Исходная ситуация: {process_option.title}",
        f"Приоритет: {priority_option.title}",
        "Интеграции: " + (", ".join(x.title for x in selected) or "Не определены"),
        "",
        "Компоненты:",
        *(f"• {item}" for item in components),
        "",
        "Этапы:",
        *(f"{i}. {item}" for i, item in enumerate(stages, 1)),
        "",
        "Проверяемые критерии:",
        *(f"• {item}" for item in acceptance),
        "",
        "Риски и ограничения:",
        *(f"• {item}" for item in risks),
        "",
        "Вопросы для уточнения:",
        *(f"• {item}" for item in questions),
        "",
        "Черновой ориентир, не смета, договор и не итоговая архитектура.",
    ]
    return Blueprint(
        sector=sector,
        title=choice.title,
        objective=priority_option.detail,
        team=team_option,
        process=process_option,
        priority=priority_option,
        integrations=selected,
        components=components,
        stages=stages,
        acceptance=acceptance,
        risks=tuple(risks),
        next_questions=questions,
        lead_url=lead_url,
        text="\n".join(lines),
    )
