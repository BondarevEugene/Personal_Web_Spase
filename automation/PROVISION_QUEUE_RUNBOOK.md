# Managed Cloud · dry-run provisioning queue recovery

This mechanism only handles `mode=dry_run` jobs. It **never calls Railway mutation APIs**.

1. Inspect your queue at `GET /api/v1/cloud/provision/queue-health` (authenticated account).
2. Run `python -m automation.provision_worker --recover --timeout-minutes 30` to mark abandoned dry-run tasks failed, recording an event.
3. Run `python -m automation.provision_worker --once` to execute queued simulations.
4. Run both actions together with `--recover --once`.

Recovery uses a compare-and-swap update and only marks jobs that have been `running` longer than the configured threshold. It does not retry failed jobs automatically. Customers may submit a fresh simulation with a **new** idempotency key. The queue dashboard counts up to the latest 500 jobs per customer and marks the sample as truncated when appropriate.

For real provider mutations, timeout recovery cannot safely assume an operation did not happen. A future live worker must reconcile remote resource IDs before retrying.
