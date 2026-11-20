# OMNIFACTORY · Content Control & SEO Insights

## What this release actually does

A protected operator console at `/support/content` makes the first phase
of editorial management possible **without editing Python files for every
journal update**.

- Works with the three allowlisted first-party journal slugs already in
  `omni_site/editorial.py`.
- Each article has a **draft** and an independent **published snapshot** in
  Neon/PostgreSQL through SQLAlchemy; saving a draft never changes public HTML.
- An operator can save, preview, publish and restore the original checked-in
  text. Restoration is immediate; the original article and URL remain.
- Editors cannot replace the slug, GitHub source URL, or product link, to
  prevent inadvertent source substitution and misleading external redirects.
- Input is plain text, bounded and validated, with Jinja HTML escaping.
- Authentication uses existing `OMNI_SUPPORT_OPERATOR_IDS` allowlist, DB
  sessions and CSRF; tenant-owned roles alone do not grant global access.
- SEO panel shows configuration checks and actual imported aggregate search
  performance, without analytics JavaScript or browser fingerprinting.

## Search Console report workflow

The operator exports a **page report** from Google Search Console as UTF-8 CSV,
selects the report date, then uploads under `/support/content`.

The CSV must contain `Page`, `Clicks`, `Impressions`; optional `Position`
is accepted. Only HTTPS URLs of the configured `OMNI_PUBLIC_BASE_URL` and
known public routes are accepted. Personal/account/private URLs, queries,
unknown origins, duplicate rows, invalid metrics, oversized CSV files and
future dates are rejected before any write.

- Maximum upload: 512 KiB; maximum 2000 page rows.
- Only aggregate daily page clicks/impressions/position are saved. No IP,
  visitor identities, user-agent, cookies, queries or customer records.
- Repeated CSV import for the same date+path updates that aggregate record,
  avoiding duplicate counts.
- Dashboard displays the **latest imported day**, not live performance,
  monthly totals or a measured lead-conversion rate.
- Search Console reporting can lag. Exports and Search Console access are
  configured by the owner; no Google account connector or API token is installed.
- The application ingress/reverse proxy must also impose request-body limits
  because streaming reads inside FastAPI do not bound the entire HTTP upload.

## Migration and deployment

Run against a direct Neon connection after backup:

```powershell
python -m alembic -c portal_alembic.ini upgrade head
python -m portal.release_doctor --production --routes --database --json
python -m ruff check .
python -m pytest -q tests/test_public_content_control_seo.py
python -m pytest -q
```

Alembic revision `20261120_portal_16` adds the article-revision and
aggregate-search-metrics tables. A fresh database must be migrated before the
operator console is used. Before migration, the checked-in journal text remains
a fallback in local development.

## Business acceptance

1. As an ordinary signed-in customer, /support/content should be 403.
2. As an allowlisted operator, open the journal, edit a paragraph, save draft.
3. Public page and article list must remain unchanged until separate Publish.
4. Verify preview does not appear publicly; after Publish, updated text appears
   and article SEO description uses the new excerpt.
5. Restore original and confirm public text returns to first-party source.
6. Attempt script injection, unexpected slug, invalid CSRF and invalid report.
7. Import a small real Search Console report, inspect clicks/impressions/CTR
   and confirm no fake data when the report is absent.
8. Check mobile layouts, keyboard navigation, actual HTTPS and Neon migrations.

## Deliberate non-goals

This is a **first operational slice**, not full multi-user headless CMS.
Editing service catalog, cases, new article slugs, media storage, scheduling,
translation approval, advanced version history, Search Console OAuth, analytics
trackers and lead-attribution are not yet implemented. Any future traffic
measurement must be explicitly sourced and privacy-reviewed.

The SEO report is not an indicator of organic traffic unless authentic
Google Search Console exports have been uploaded. Search ranking and
conversion improvements are not guaranteed.
