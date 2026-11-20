# OMNIFACTORY / Public Performance Consolidation — Homepage CSS

## Goal

The previous Chromium baseline in PR #73 passed 36/36 viewports, and the
static-inventory report showed **22 distinct first-party CSS/JS assets,
146,960 bytes across the audited pages**. This does not mean those files
were all loaded on the homepage: the homepage itself linked 10 first-party
stylesheets, creating 10 blocking CSS requests.

This release bundles those 10 sheets into **one CSS response** in their
original cascade order, preserving existing corporate design, layouts,
creative typography, CRM and Experience Lab interactions.

## Reproducible build

The human-authored CSS remains in the original files:
`site.css`, `platform.css`, `founders.css`, `unified_shell.css`,
`public_growth.css`, `demo_home.css`, `case_home.css`,
`services_home.css`, `trust_home.css`, `visual_excellence.css`.

The generated product asset is
`omni_site/static/home.bundle.css`.

To update or verify:

```powershell
python -m scripts.build_public_styles --write
python -m scripts.build_public_styles --check
python -m ruff check scripts/build_public_styles.py tests/test_home_css_bundle.py scripts/public_ux_audit.py scripts/public_asset_budget.py tests/test_public_qa_contract.py
python -m pytest -q tests/test_home_css_bundle.py tests/test_public_visual_excellence.py
```

`--check` exits nonzero if the compiled bytes differ from the authored
sources; CI now blocks a stale bundle. The build performs **no
minification**, so it cannot silently change selectors, URL paths or
CSS logic. Import order and font import are preserved. The remaining
public routes continue using their existing stylesheets.

## What is measured and what is not

- **Before:** 10 local first-party CSS `<link rel="stylesheet">` tags on `/`.
- **After:** 1 local CSS link on `/`, confirmed by route tests and Chromium.
- The shared bundle contains the same CSS rules. Its raw CSS bytes are
  approximately the sum of the input sheets, with delimiters added.
- The reduction in browser request count is real, but improvement in LCP,
  INP or CLS is **not established** until testing on the actual deployment.
- Future measurements should compare browser network waterfall, main-thread
  render and transfer-size/cache results under matching conditions.
- Other public and operator pages are unchanged; none of their asset
  dependencies are merged.

## Deployment and cache considerations

The new homepage references `/studio-assets/home.bundle.css?v=1`.
If a later release changes the bundle, **increment its query version** in
`index.html` to prevent old intermediary caches from serving stale CSS.
For long-lived immutable caching a future phase can move to content-hashed
filenames and deploy-time asset manifests.

## Acceptance

1. CI must pass Ruff for QA/build modules, the public pytest suite, the
   bundle generation drift check, the asset report and 36 Chromium views.
2. In GitHub Actions download the `omnifactory-public-quality` artifact.
   Inspect the real mobile and desktop homepage screenshots and the browser
   report; the count of local stylesheets should be 1 for the homepage.
3. Verify `/` at 360/430/768/1440 pixels, particularly the header
   overflow repaired in #73, corporate card colors and sticky contact CTA.
4. Test the real Studio form, Graph Studio, Experience Lab, calculator,
   cases, journal, trust center and protected account login.
5. Edit the homepage H1 in Creative Content Studio to verify that the
   original text-substitution contract still works.
6. Check /studio and secondary public pages still load their original CSS.

No new database tables, credentials, new browser scripts, live analytics
trackers or claims about unmeasured performance.
