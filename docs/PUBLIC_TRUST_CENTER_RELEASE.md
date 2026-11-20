# OMNIFACTORY Public Trust Center

## Public experience

- `/trust`: substantive disclosure hub, based on verified platform code.
- `/trust/process`: discovery → scoped MVP → development/testing → review and rework.
- `/trust/security`: tenant separation, CSRF, sessions, project files and
  deployment-specific controls, plus missing certifications and MFA.
- `/trust/questions`: how costs/schedules are scoped, what integrations require,
  deliverables and how to submit a request.
- Homepage, services, cases and engineering journal lead to the trust hub.
- Real `/studio#contact` is the only lead form. This release creates no new
  storage of visitors' information.
- These pages appear in the HTTPS-origin-controlled public sitemap.

## Truth and privacy boundaries

Do not turn source-code implementations into contractual security warranties.
Specifically:
- No claim of SOC 2 / ISO 27001 certification or independent audit.
- No claim of universal MFA, electronic signatures or guaranteed file deletion.
- Do not suggest that the presence of a payment webhook equals live acquiring.
- Current project-attachment limits and private database storage are technical
  design decisions, not a blanket data-retention promise.
- Real customer agreements, data handling terms, privacy policy, and production
  infrastructure require separate legal and technical review.

These pages are explanatory product content, **not a substitute for a
company-specific privacy policy, a binding service agreement or a DPA**.

## Tests and go/no-go

    python -m ruff check .
    python -m pytest -q tests/test_public_trust_center.py tests/test_public_services_conversion.py tests/test_public_case_library.py
    python -m pytest -q

Manual checks:
1. Navigate `/` → `/trust` → all three pages → real case and Studio contact.
2. Verify separate title/meta descriptions, one H1 and readable mobile layout.
3. Open TOC links by keyboard and make sure anchor scroll positions are clear.
4. Test the live Studio lead delivery route before advertising its availability.
5. Confirm public sitemap with deployed HTTPS `OMNI_PUBLIC_BASE_URL`.
6. Review security claims against deployed Neon/HTTPS/backup reality before
   publishing a commercial guarantee.

No new database migrations or external integrations. No SEO rankings promised.
