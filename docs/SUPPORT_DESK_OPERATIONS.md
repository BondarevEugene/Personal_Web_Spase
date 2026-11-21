# OMNIFACTORY · Service Desk Operations

This release adds operator-side review to the existing customer service desk. It does not create a public admin account or grant all organization owners platform-wide access.

## Access / onboarding

1. Register or sign in as a normal OmniFactory customer at `/account/login`.
2. Look up that account's exact `portal_customers.id` UUID via trusted database administration (not from arbitrary client-submitted data).
3. Configure `OMNI_SUPPORT_OPERATOR_IDS` as a comma-separated list of those UUIDs in the server environment. An unset/empty allowlist grants **no operator access**.
4. Restart the service and visit `/support/desk` on HTTPS (local 127.0.0.1 HTTP is accepted for development only).

Do not use organization `role=owner` as proof of platform operator permissions. Never hardcode the operator UUID in source control.

## Lifecycle

`new → review → approved → in_progress → resolved → closed`

Additional guarded transitions support `waiting_customer`, cancellation via `closed`, and reopening from `closed` to `review`. Only a platform operator can change status, and every transition is saved to `portal_support_events`. Public client comments use `portal_support_messages`. The operator can assign the ticket to another allowlisted operator.

No email notifications, SLA tracking, file uploads, payment capture or simulated service metrics are introduced here. Those require separately tested integrations.

## Safe rollout

- Migrate **the selected environment only** with `python -m alembic -c portal_alembic.ini current` then `upgrade head`, after taking a backup.
- The new revision is `20261119_portal_12` and depends on `20261119_portal_11`.
- Use the same selected virtualenv for server, tests and Alembic. For local development the known-good environment was `.venv-omni`.
- Run `python -m pytest tests/test_portal_support_operator.py tests/test_portal_support_surface.py -q`, full pytest and Ruff before merging.
- Test that an ordinary customer gets 403 for `/support/desk` and cannot read another organization's `/account/tickets/{ticket_id}`.
- Test status changes, assignment, public replies and customer-visible status history in a disposable local database.

## Known limitation

The operator access list is intentionally environment-configured for this release rather than editable by a client. A full administrative IAM/roles interface needs its own security review.
