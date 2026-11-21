# OmniFactory Platform — Railway release runbook

## Objective
Deploy the current FastAPI platform (server:app), not legacy OmniFactory EVO.
Production domain: omnifactory.up.railway.app. Do not switch production before staging acceptance.

## staging
1. Merge reviewed integration changes into main only after CI passes.
2. Create a separate Railway staging service/environment at a release commit with a temporary domain.
3. Preserve the previous successful production deployment for rollback.
4. Match Railway domain target port to the container PORT. Dockerfile binds 0.0.0.0 on the injected PORT (default 8080).
5. Use a separate Neon staging database. Configure OMNI_PORTAL_DATABASE_URL and OMNI_PORTAL_MIGRATION_URL (direct Neon endpoint for migrations).
6. Configure staging session, OAuth, billing, Telegram and webhook settings safely. Never expose production credentials.

## Neon migrations
- Back up production and verify a restore before production release.
- Run python -m alembic -c portal_alembic.ini current
- Run python -m alembic -c portal_alembic.ini heads
- Run python -m alembic -c portal_alembic.ini upgrade head against staging first.
- Confirm schema, customer and project data. Review backward compatibility.
- Do not run destructive migrations automatically at every web startup.

## Staging acceptance
- GET /health returns HTTP 200 and platform_ui=studio-v3-platform.
- GET / shows the new public homepage, not MAIN_NODE or BUILDER_PRO.
- GET /services and GET /services/ai-solutions return 200.
- GET /architect and GET /automation/studio show usable pages.
- GET /account redirects unauthenticated users or renders workspace when authenticated.
- Verify login, CSRF, logout, language, project detail, documents, approvals and notifications.
- Verify mobile layout, browser console, assets, response time and memory.
- Verify all required CI workflows and migration checks.

## Production cutover
1. Record prior deployment ID, git SHA, database revision and domain target port.
2. Deploy reviewed commit after staging acceptance.
3. Apply approved production migrations once with a verified backup.
4. Verify port mapping and monitor /health, homepage, login, builder and automation.
5. Watch HTTP 5xx and errors; keep rollback available.

## rollback
- Redeploy previous known-good image/commit and restore previous service variables.
- Database rollback is not code rollback. For incompatible schema changes use a tested restore or forward-fix plan.
- Stop cutover if customer data, authentication, payments or callbacks fail.

## Status
This is release configuration and verification guidance, not evidence that staging or production cutover has occurred.
