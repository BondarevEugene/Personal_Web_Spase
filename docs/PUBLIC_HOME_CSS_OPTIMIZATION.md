# OMNIFACTORY · Homepage CSS request optimization

## Measured baseline and change

PR #73 established a passing 36-view Chromium quality gate and a public asset
inventory. An inspection of the homepage HTML on the post-#73 working branch
found **ten blocking stylesheet links**: one reusable base `site.css` and
nine homepage-specific feature stylesheets.

This release preserves the shared base CSS and joins the nine independent
feature CSS files into one generated, ordered bundle:

- BEFORE: 10 same-origin CSS requests to render the homepage.
- AFTER: 2 same-origin CSS requests (base + feature bundle).
- Source CSS remains unchanged and accessible individually for other pages.
- No extra JavaScript, external UI dependencies, fonts or images.
- Reduces request overhead, **not necessarily transfer bytes**, since the
  bundle is derived from the same CSS; network-level performance gains must
  be measured rather than assumed.

## How the bundle is generated

`scripts/build_home_css.py` reads these files in precise cascade order:
`platform.css`, `founders.css`, `unified_shell.css`,
`public_growth.css`, `demo_home.css`, `case_home.css`,
`services_home.css`, `trust_home.css`, `visual_excellence.css`.

The generated `omni_site/static/home_features.bundle.css` is committed
alongside the sources so local/production environments do **not** need a build
step during web startup.

```powershell
python -m scripts.build_home_css
python -m scripts.build_home_css --check
```

Whenever one of the nine source stylesheets changes, regenerate the bundle
and commit it. CI refuses a stale generated artifact.

`site.css` remains separate because it is shared by other public pages and
contains the existing Google Fonts @import. Combining it could break the
CSS import order or duplicate the shared cached base on every destination.

## Acceptance and regression checks

```powershell
python -m ruff check scripts/build_home_css.py tests/test_public_home_css_bundle.py
python -m pytest -q tests/test_public_home_css_bundle.py
python -m pytest -q tests/test_public_visual_excellence.py
python -m scripts.build_home_css --check
```

The existing public-browser GitHub Actions workflow runs these checks along
with the public suite, CSS/JS inventory and Chromium checks at
360/430/768/1440px.

Manual QA:
1. Compare the homepage at phone and desktop widths with the previous PR #73
   screenshots: spacing, fonts, components, icons and responsive rules.
2. Check DevTools: exactly two same-origin CSS stylesheet links on the homepage.
3. Check the calculator, three homepage actions, mobile menu, mobile contact
   CTA and the Experience Lab links.
4. Verify public services, cases, journal, trust, and Studio still load the
   common base CSS as before.
5. Run production PageSpeed/Lighthouse on the same URL before and after
   deploying, recording measured request count and LCP/INP/CLS.
6. Keep the real technical case images as placeholders until approved
   screenshots can replace them.

## Scope

No new database tables or Neon migrations. No change to protected CRM,
payments, authentication or visitor data processing. No invented page
speed scores or SEO rankings.
