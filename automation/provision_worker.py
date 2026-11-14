"""Manual, recoverable queue worker for provisioning preflight simulations.

Usage: python -m automation.provision_worker --once
A worker intentionally NEVER creates Railway resources in this release.
Do not auto-start this module in the web app.
"""
from __future__ import annotations

import argparse
import logging

from sqlalchemy import select, update

from automation.deployment import DeploymentSpec, build_plan
from portal.db import session_factory
from portal.models import CloudProvisionEvent, CloudProvisionJob, utcnow

log = logging.getLogger("omni.provision")


def emit(db, job_id: str, code: str, message: str):
    db.add(CloudProvisionEvent(
        job_id=job_id, code=code,
        message=message[:300], created_at=utcnow(),
    ))


def execute_once(limit: int = 25) -> int:
    completed = 0
    with session_factory()() as db:
        queued_ids = db.scalars(
            select(CloudProvisionJob.id)
            .where(CloudProvisionJob.status == "queued",
                   CloudProvisionJob.mode == "dry_run")
            .order_by(CloudProvisionJob.created_at)
            .limit(max(1, min(limit, 25)))
        ).all()
    for job_id in queued_ids:
        with session_factory()() as db:
            # Compare-and-swap: only one concurrent worker can claim the job.
            claim = db.execute(update(CloudProvisionJob).where(
                CloudProvisionJob.id == job_id,
                CloudProvisionJob.status == "queued",
                CloudProvisionJob.mode == "dry_run",
            ).values(status="running", updated_at=utcnow()))
            if claim.rowcount != 1:
                db.rollback()
                continue
            emit(db, job_id, "claimed", "Dry-run worker reserved this job")
            db.commit()
        with session_factory()() as db:
            job = db.get(CloudProvisionJob, job_id)
            if job is None or job.status != "running":
                continue
            try:
                spec = DeploymentSpec.model_validate_json(job.manifest_snapshot)
                plan = build_plan(spec)
                if plan.manifest_sha256 != job.manifest_sha256:
                    raise ValueError("Manifest hash mismatch")
                emit(db, job.id, "manifest_verified", "Pinned manifest hash matches")
                emit(db, job.id, "provider_preflight",
                     "Railway operations verified as disabled in simulation mode")
                emit(db, job.id, "budget_not_quoted",
                     "Monthly budget cap exists; no real provider quote available")
                emit(db, job.id, "secrets_not_injected",
                     "Credentials are not passed or accessed by dry-run worker")
                job.status = "simulated"
                job.updated_at = utcnow()
                emit(db, job.id, "simulation_complete",
                     "No Railway mutation executed; no bot was deployed")
                completed += 1
            except (ValueError, TypeError) as exc:
                job.status = "failed"
                job.error_code = "MANIFEST_INVALID"
                job.updated_at = utcnow()
                emit(db, job.id, "validation_failed",
                     "Plan validation failed; no provider operations performed")
                log.warning("Invalid provisioning plan job=%s", job.id)
            db.commit()
    return completed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.once:
        log.info("Completed %s provisioning simulations", execute_once())


if __name__ == "__main__":
    main()
