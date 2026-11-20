"""Deterministic, downloadable preliminary technical specification.

This is a planning artifact, not an approved implementation contract.
No user-provided prose is accepted and no customer data is persisted.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from omni_site.blueprint_studio import Blueprint, make_blueprint


@dataclass(frozen=True)
class Specification:
    revision: str
    markdown: str
    blueprint: Blueprint


def _items(values: tuple[str, ...]) -> str:
    return "\n".join(f"- {value}" for value in values)


def compile_specification(
    *,
    sector: str,
    team: str,
    process: str,
    priority: str,
    integrations: tuple[str, ...] = (),
) -> Specification:
    """Build the same document for the same canonical selection, every time."""
    # A fixed order prevents checkbox order from changing document identity.
    canonical = tuple(sorted(integrations))
    brief = make_blueprint(
        sector=sector,
        team=team,
        process=process,
        priority=priority,
        integrations=canonical,
    )
    fingerprint = "|".join((sector, team, process, priority, *canonical))
    revision = sha256(fingerprint.encode("utf-8")).hexdigest()[:12]
    dependencies = (
        "Подтвердить владельца процесса и ответственного за приёмку",
        "Согласовать источники данных, сроки хранения и доступы",
        "Предоставить документацию и тестовый доступ для выбранных API",
        "Утвердить границы MVP, критерии приёмки и план отката",
    )
    nonfunctional = (
        "Серверная проверка входных данных и ограничение прав доступа",
        "Наблюдаемость: структурированные ошибки и журнал ключевых операций",
        "Резервное копирование, проверка восстановления и миграции схемы",
        "Повторяемое развёртывание и автоматизированные регрессионные проверки",
    )
    exclusions = (
        "Стоимость и сроки без обследования не фиксируются",
        "Внешние API и платежи не считаются подключёнными",
        "Этот документ не создаёт проект, заказ или договор",
        "Персональные данные и секреты в документ не включаются",
    )
    milestones = "\n".join(
        f"{number}. **Этап {number}:** {stage}\n"
        f"   - Результат: проверяемый артефакт и протокол приёмки"
        for number, stage in enumerate(brief.stages, 1)
    )
    markdown = (
        "# OMNIFACTORY / Предварительное техническое задание\n\n"
        f"**Идентификатор редакции:** `{revision}`  \n"
        "**Статус:** черновик для обсуждения, не утверждённое ТЗ\n\n"
        "## 1. Контекст\n\n"
        f"- Продукт: {brief.title}\n"
        f"- Команда: {brief.team.title}\n"
        f"- Текущий процесс: {brief.process.title}\n"
        f"- Приоритет: {brief.priority.title}\n"
        f"- Цель: {brief.objective}\n"
        "- Интеграции: "
        + (", ".join(item.title for item in brief.integrations) or "не определены")
        + "\n\n"
        "## 2. Предварительная архитектура\n\n"
        + _items(brief.components)
        + "\n\n## 3. Этапы и результаты\n\n"
        + milestones
        + "\n\n## 4. Критерии приёмки\n\n"
        + _items(brief.acceptance)
        + "\n\n## 5. Нефункциональные требования\n\n"
        + _items(nonfunctional)
        + "\n\n## 6. Риски и ограничения\n\n"
        + _items(brief.risks)
        + "\n\n## 7. Зависимости до старта\n\n"
        + _items(dependencies)
        + "\n\n## 8. Открытые вопросы\n\n"
        + _items(brief.next_questions)
        + "\n\n## 9. Вне согласованного объёма\n\n"
        + _items(exclusions)
        + "\n\n## 10. Порядок согласования\n\n"
        "Заказчик уточняет требования, исполнитель подтверждает "
        "реализуемость, стороны отдельно утверждают объём, стоимость, "
        "сроки и критерии приёмки.\n"
    )
    return Specification(revision=revision, markdown=markdown, blueprint=brief)
