"""Read-only project progress based strictly on persisted milestone states.

A stage-count ratio is not a time, budget or work-completion estimate.
"""
from __future__ import annotations

from collections import Counter


def milestone_progress(milestones):
    stages = list(milestones)
    counts = Counter(stage.status for stage in stages)
    total = len(stages)
    completed = counts["completed"]
    return {
        "total": total,
        "completed": completed,
        "in_progress": counts["in_progress"],
        "planned": counts["planned"],
        "percent": round(completed * 100 / total) if total else None,
        "label": "Завершено этапов",
        "is_estimate": False,
    }
