# OMNIFACTORY Public Journal + Scenario ROI + Conversion

This is a stacked release **built on PR #63**, branch
`feat/public-growth-experience-20261120`. Merge #63 first; then retarget
this PR to `feat/founders-omni-editorial-20261116` and re-run CI.

## Scope
- `/journal` public index and three SEO-friendly articles under `/journal/{slug}`.
- Every article is explicitly attributed to its own repository and states
  implementation boundaries; no invented customer reviews or revenue figures.
- Graph Studio: Pydantic node graph, Python aiogram ZIP, mock-transport tests,
  and in-memory cursor limitation.
- Client Workspace: separate customer projects, milestones, document revisions,
  owner approvals, revision loop, tenant isolation, and private bounded files.
- Food_Porn: aiogram digital menus and wish collages, user media workflow,
  generated assets, and backend payment validation concepts. Provider production
  status is NOT claimed.
- Homepage links to the journal and its three articles.
- Business calculator includes **illustrative, editable** project-type inputs,
  never labeled measured Food_Porn/CRM/Graph Studio productivity or conversion.
- A final conversion section links directly to the existing Studio contact form.
- Journal routes added to the HTTPS-origin-controlled public sitemap.

## Important truth boundaries
The preset values are examples to explain the formula, not survey data,
observed results, expected client ROI or a forecast. The client must supply
their own operation counts, labor costs and realistic automation assumptions.
No user input is transmitted, stored or tracked by this UI.

CRM marketing article covers the verifiable Client Workspace module of
Personal_Web_Spase. It does not claim that an independent CRM repository's
unverified features are complete.

## Acceptance
```powershell
python -m ruff check .
python -m pytest -q tests/test_public_growth_experience.py tests/test_public_engineering_journal.py
python -m pytest -q
```

Manual browser checks: start at `/`, choose all three calculator presets,
edit fields by hand, view the three article pages, verify table of contents
anchors, source links and CTAs, check on small mobile viewport and with keyboard.
Check `/sitemap.xml` with a real HTTPS `OMNI_PUBLIC_BASE_URL`. Since there
is no canonical URL without the configured domain, do not generate one from
untrusted request Host.

## Growth measurement (after deployment)
Measure organic impressions/clicks/CTR in Search Console, article-to-Studio
contact clicks, real submitted lead rate, and Web Vitals. Implement a
consent-aware analytics pipeline before any tracking. No promised ranking.
