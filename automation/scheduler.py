"""Opt-in, DB-backed recurring Automation worker.

Run manually: python -m automation.scheduler --once
Run as a separately managed service: python -m automation.scheduler --loop

No worker starts from FastAPI and no external side effects occur: schedules
execute dry-runs only until an operator-approved, idempotent live executor exists.
"""
from __future__ import annotations

import argparse
import logging
import time
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError

from api.automation import record_run
from portal.db import session_factory
from portal.models import AutomationSchedule, AutomationWorkflow, utcnow

log = logging.getLogger("omni.scheduler")


def tick() -> int:
    now = utcnow()
    completed = 0
    with session_factory()() as db:
        due = db.scalars(
            select(AutomationSchedule).where(
                AutomationSchedule.enabled.is_(True),
                AutomationSchedule.next_run_at <= now,
            ).order_by(AutomationSchedule.next_run_at).limit(25)
        ).all()
        jobs = [(row.id, row.next_run_at, row.interval_minutes, row.workflow_id)
                for row in due]
    for id, due_at, interval, workflow_id in jobs:
        # Atomic compare-and-swap ensures two workers cannot claim same tick.
        with session_factory()() as db:
            new_due = now + timedelta(minutes=interval)
            claimed = db.execute(
                update(AutomationSchedule).where(
                    AutomationSchedule.id == id,
                    AutomationSchedule.enabled.is_(True),
                    AutomationSchedule.next_run_at == due_at,
                ).values(next_run_at=new_due, updated_at=now)
            )
            db.commit()
            if claimed.rowcount != 1:
                continue
            workflow = db.get(AutomationWorkflow, workflow_id)
            if not workflow:
                log.error("Missing workflow for schedule %s", id)
                continue
            key = "scheduled:" + id + ":" + str(int(due_at.timestamp()))
            try:
                result = record_run(db, workflow, input_data={}, live=False,
                                    idempotency_key=key)
                completed += 1
                log.info("Schedule %s run=%s status=%s", id, result["id"],
                         result["status"])
            except Exception:
                # Never retry automatically: a recorded failure must be inspected.
                log.exception("Schedule %s failed", id)
    return completed


def main() -> None:
    parser = argparse.ArgumentParser(description="OmniFactory schedule worker")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true", help="Process due schedules once")
    mode.add_argument("--loop", action="store_true", help="Keep processing every 30 seconds")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.once:
        log.info("Processed %s due schedules", tick())
        return
    try:
        while True:
            log.info("Processed %s due schedules", tick())
            time.sleep(30)
    except KeyboardInterrupt:
        log.info("Scheduler stopped")


if __name__ == "__main__":
    main()
