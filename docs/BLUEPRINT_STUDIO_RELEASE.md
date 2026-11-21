# OMNIFACTORY — Blueprint Studio / Scope-to-Architecture v1

## Why this is a product upgrade

The existing Experience Lab illustrates the engineering routes for CRM,
Telegram and automation. The new `/demo/blueprint` converts that passive
demonstration into a **working preliminary project brief**. Visitors select
business parameters, review a reproducible architectural outline and can
copy or print it before sending an inquiry.

This **does not** execute a third-party integration, estimate an exact
project price, create a CRM order or claim an approved technical design.

## Workflow

The UI asks only about the **type of project**, **team size**,
**process maturity**, **priority** and optionally up to four named integrations.
No names, phone numbers, email addresses or uploaded documents are requested.

The FastAPI `GET /demo/blueprint` serves a complete, indexable form.
The `POST /demo/blueprint` validates a fixed, documented vocabulary and
returns, in memory only:
- reference Python/FastAPI/aiogram/SQLAlchemy components as relevant;
- phased discovery, development, testing and transfer plan;
- measurable functional acceptance conditions;
- risk and integration boundaries;
- explicit follow-up questions;
- copyable plaintext project brief and print-friendly page.

On POST, headers are `Cache-Control: no-store` and
`X-Robots-Tag: noindex, nofollow`, preventing personal or session-dependent
results from being cached or indexed.

The user can click a CTA to the **existing** Studio contact form. Only a
predefined service **topic** is included in its URL; neither the brief nor
the answers are transmitted via the link. The visitor can paste the brief
themselves. The existing lead form handles actual contact submissions.

## Architecture and privacy

- `omni_site/blueprint_studio.py`: pure deterministic Python logic,
  bounded catalogs and structured return value. No OpenAI API or external API.
- `omni_site/router.py`: stateless GET+POST endpoints placed before the
  existing dynamic `/demo/{slug}` route.
- `omni_site/templates/blueprint_studio.html`: semantic radio groups,
  optional integration checkboxes, architecture details, accessible text
  export and real lead CTA.
- `omni_site/static/blueprint_studio.css`: premium graphite/violet technical
  art direction, responsive form and print media.
- `omni_site/static/blueprint_studio.js`: clipboard and print only; no
  tracking, cookies, localStorage or analytics.
- The core Experience Lab has a prominent entry point. The public
  `sitemap.xml` includes only the GET form URL.

This release needs **no database migration, Neon schema updates,
client-session logic, premium API credentials or external JavaScript SDKs**.

## Technical acceptance

```powershell
python -m ruff check omni_site/blueprint_studio.py tests/test_public_blueprint_studio.py
python -m pytest -q tests/test_public_blueprint_studio.py
python -m pytest -q tests/test_public_solution_experience.py
python -m pytest -q
```

The existing Chromium workflow extends from 36 to **40** public viewport
checks (10 pages × 360/430/768/1440 px). It submits the default Blueprint
form, verifies four architecture panels and confirms the plaintext brief.

Manual:
1. Open `/demo`, follow `/demo/blueprint`, submit CRM with defaults.
2. Change business area to Telegram and Automation and compare components.
3. Select external API, payments, legacy system and 31+ team; verify
   idempotency, API sandbox, migration and role-audit conditions appear.
4. Submit missing/invalid data: receive HTTP 422; no error triggers an order.
5. Copy via a secure-browser clipboard or select text manually, print to PDF
   with the built-in browser, and follow the real Studio contact link.
6. Check mobile widths 360 and 430, keyboard access, visible focus, and
   reduced motion.
7. Inspect network: form POST stays on the same host and no analytics events
   are emitted. Check the deployment's HTTPS and reverse proxy.
8. Do not present this output as legally binding scope, a guaranteed duration,
   a price quote, independent security audit or live workflow.

## Creative direction

Preserve OMNIFACTORY's clean near-black backdrop, disciplined typography,
controlled purple accent and schematic, clearly **illustrative** engineering
visuals. Existing image placeholders remain unchanged.
