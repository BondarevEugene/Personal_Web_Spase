"""Project planning data contracts and Gantt computations."""
from datetime import datetime
from types import SimpleNamespace

import pytest

from portal.project_work import validate_task_dates


def test_dates_accept_open_and_ordered_ranges():
    validate_task_dates(None, None)
    validate_task_dates(datetime(2026, 11, 20), datetime(2026, 11, 20))


def test_dates_reject_reversed_range():
    with pytest.raises(ValueError):
        validate_task_dates(datetime(2026, 11, 21), datetime(2026, 11, 20))


def test_task_models_have_project_and_actor_foreign_keys():
    from portal.models import ClientProjectTask, ClientProjectTimeEntry

    task = ClientProjectTask(project_id="p", title="Task", estimate_minutes=120)
    entry = ClientProjectTimeEntry(task_id="t", actor_id="a", minutes=30, note="Work")
    assert task.project_id == "p"
    assert task.estimate_minutes == 120
    assert entry.actor_id == "a"


def test_gantt_dates_are_not_invented():
    from portal.project_work import validate_task_dates

    task = SimpleNamespace(start_on=None, due_on=None)
    assert task.start_on is None and task.due_on is None
    validate_task_dates(task.start_on, task.due_on)
