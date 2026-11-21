# OMNIFACTORY — Public Case Library / Verified Portfolio

## Context and merge policy

PR #64 was merged into the feature branch of PR #63, not directly into the
working base. This release is branched from the **actual PR #64 head** and
targets the working platform branch. Thus the new PR can carry the engineering
journal and the new case library together, avoiding silently lost features.

## Feature set

- /cases — four real first-party cases with lightweight local filtering:
  Graph Studio, Client Workspace, Food_Porn, Automation Studio.
- /cases/{slug} — product architecture, scope, limitations, technology stack,
  existing product route, first-party code reference and engineering journal.
- Shared case data in omni_site/case_library.py; only fixed, reviewed slugs
  are served. Unknown slugs return 404.
- The preview is a semantic HTML **schematic architectural overview**,
  explicitly labeled NOT A SCREENSHOT. No fabricated product images, clients,
  metrics, ratings, live production claims or screenshots.
- Homepage / and existing /projects link to the case library.
- Canonical sitemap extends /cases and all individual case URLs when the
  operator has configured an HTTPS OMNI_PUBLIC_BASE_URL.
- The case filter uses no API, cookies, localStorage or tracking; all cases
  are visible without JavaScript. Buttons expose aria-pressed status and
  the count region uses aria-live.

## Remaining work, intentionally not faked

- Actual screenshots require visiting authenticated real product pages with
  stable demo data, redacting names/emails/tokens before publishing, then
  adding optimized WebP/AVIF and descriptive alt text.
- Do not show client-owned files, logs, personal photos or live credentials.
- The independent OmniFactory CRM repository was not independently verified
  in this release; its marketing promise is not added to the case catalog.
- Production status is intentionally not inferred from source-code presence.

## Acceptance checklist

    python -m ruff check .
    python -m pytest -q tests/test_public_case_library.py tests/test_public_engineering_journal.py tests/test_public_growth_experience.py
    python -m pytest -q

Manual:
- Review /cases, each /cases/<slug>, /projects and homepage links.
- Filter all categories, confirm labels and back/forward behavior.
- Verify small mobile screen, keyboard, contrast, reduced-motion preference.
- Validate GitHub source links and journal references.
- Check /sitemap.xml only after real HTTPS OMNI_PUBLIC_BASE_URL is configured.
- Verify all actual claims against working product demonstrations and tests.

## SEO measurement

Submit the public sitemap to Search Console, inspect indexing coverage,
organic impressions/CTR, article-to-case navigation and real leads. Results
are not guaranteed by styling. Consent and privacy policy are needed before
adding behavior analytics.
