"""Workspace progress must never invent estimates or completion."""
from types import SimpleNamespace

from portal.project_progress import milestone_progress


def test_no_milestones_has_unknown_progress():
    progress = milestone_progress([])
    assert progress["percent"] is None
    assert progress["total"] == 0


def test_progress_counts_only_completed_stages():
    stages = [SimpleNamespace(status=s) for s in (
        "completed", "in_progress", "planned", "completed",
    )]
    progress = milestone_progress(stages)
    assert progress["completed"] == 2
    assert progress["in_progress"] == 1
    assert progress["planned"] == 1
    assert progress["percent"] == 50
    assert progress["is_estimate"] is False


def test_progress_is_not_a_time_estimate():
    stages = [SimpleNamespace(status="in_progress")]
    assert milestone_progress(stages)["percent"] == 0
