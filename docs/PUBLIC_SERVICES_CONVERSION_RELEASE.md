# OMNIFACTORY — Public Service Pages / Conversion Workflow

## Goal

Turn the engineering public site into a clear route from business problem
to a credible technical service and the existing Studio inquiry form.
Real product source and actual working pages support each service; stock
numbers, fake testimonials and invented delivery dates are never used.

## Public routes

| Route | Purpose |
| --- | --- |
| /services | Directory of CRM, Telegram, business automation |
| /services/custom-crm | Customer and operator workspaces, CRM backend |
| /services/telegram-bots | Telegram dialogue products / aiogram |
| /services/business-automation | Workflows, API integration, dry-run |
| /cases | Verifiable first-party product architecture |
| /studio#contact | Existing lead form, no duplicate backend |

Each service includes audience, deliverables, process, boundaries, relevant
first-party case, technical notes and FAQ. All links are static allowlisted
paths, not generated from end-user input.

## Real inquiry handoff

Clicking "Обсудить эту задачу" opens
`/studio?topic=<encoded approved service topic>#contact`.
Studio's current JS selects a matching *existing* option in the topic select.
It does NOT automatically submit a lead, prefill personal information,
store the query in a cookie, or add a new lead API. An invalid topic is ignored.

Existing `/studio/api/lead` integration requires valid server-side
configuration for actual delivery. If Telegram delivery is unavailable, the
current Studio form reports an error and does not invent success.

## SEO and performance

Add /services and three detail routes to the explicit public sitemap.
Each page has its own title, description and headings. The visual system
uses static CSS and accessible native HTML for FAQs, no heavy JS framework.
Do not invent canonical URLs until a real public HTTPS origin is configured.

## Acceptance

    python -m ruff check .
    python -m pytest -q tests/test_public_services_conversion.py
    python -m pytest -q

Manual:
1. Open the homepage → /services → each service → /studio#contact.
2. Verify the selected topic on Studio; an invalid URL param must do nothing.
3. Check links to each real case and related engineering journal article.
4. Check narrow Android viewport, keyboard navigation and focus indicators.
5. Verify sitemap only with a real OMNI_PUBLIC_BASE_URL.
6. Check the lead backend with real test delivery before advertising active
   response channels; never log or expose bot token / private chat IDs.

No new database tables, payments or production integrations are claimed.
No automatic ranking or traffic growth is promised.
