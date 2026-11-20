"""Shared, tenant-neutral task summary; routes enforce authorization."""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select

from portal.models import ClientProjectTask, ClientProjectTimeEntry


def task_context(db, project_id):
    tasks = db.scalars(select(ClientProjectTask).where(
        ClientProjectTask.project_id == project_id,
    ).order_by(ClientProjectTask.created_at, ClientProjectTask.id).limit(200)).all()
    ids = [task.id for task in tasks]
    entries = db.scalars(select(ClientProjectTimeEntry).where(
        ClientProjectTimeEntry.task_id.in_(ids),
    ).limit(5000)).all() if ids else []
    logged = defaultdict(int)
    for entry in entries:
        logged[entry.task_id] += entry.minutes
    dates = [d for task in tasks for d in (task.start_on, task.due_on) if d]
    origin = min(dates).date() if dates else None
    finish = max(dates).date() if dates else None
    span = max(1, (finish - origin).days + 1) if origin else 1
    bars = []
    for task in tasks:
        if task.start_on and task.due_on and origin:
            offset = (task.start_on.date() - origin).days
            duration = (task.due_on.date() - task.start_on.date()).days + 1
            bars.append((task, round(100 * offset / span, 2),
                         round(100 * duration / span, 2)))
    return {
        "work_tasks": tasks,
        "work_logged": dict(logged),
        "work_estimate_minutes": sum(task.estimate_minutes for task in tasks),
        "work_actual_minutes": sum(logged.values()),
        "gantt_bars": bars,
        "gantt_origin": origin,
        "gantt_finish": finish,
    }


def validate_task_dates(start, due):
    if start and due and due < start:
        raise ValueError("Дата завершения раньше даты начала")
    if start and due and due - start > timedelta(days=3650):
        raise ValueError("План задачи превышает 10 лет")
