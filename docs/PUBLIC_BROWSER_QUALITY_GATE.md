# OMNIFACTORY Public Browser Quality Gate

## Why

Public routing and FastAPI/pytest contracts already exist, but they cannot
tell whether a phone-sized viewport has horizontal overflow, a mobile menu
does not open, or a JavaScript interaction has stopped working. This release
adds a **real Chromium smoke test** to CI and an exact public CSS/JS inventory.
The work is read-only; there are no live customer operations or external leads.

## New verification layers

### A. Browser experience

Run:

```powershell
python -m pip install "playwright>=1.50,<2"
python -m playwright install chromium
python -m uvicorn server:app --host 127.0.0.1 --port 8765
# In another terminal:
python -m scripts.public_ux_audit --base-url http://127.0.0.1:8765
```

The script visits nine public paths at **360, 430, 768, 1440px** (36 views):
homepage, service directory and CRM service, case library and Graph Studio
case, journal, trust center, Experience Lab and its Telegram deep link.

It asserts: HTTP 200, an H1 and title, lack of document horizontal overflow,
JS exceptions, the homepage's three real business routes, visible mobile
contact CTA, working mobile navigation, catalog links, and five-step
Experience Lab interactions.

Reports:
- `artifacts/public-ux/report.json`: structured results and DOM navigation
  observations, clearly labeled local measurements.
- `artifacts/public-ux/report.md`: compact PASS/FAIL view matrix.
- `artifacts/public-ux/screenshots`: actual browser screenshots of PUBLIC
  home and demo pages at selected widths. Not synthetic screenshots.

### B. Real public CSS/JS inventory

Run:

```powershell
python -m scripts.public_asset_budget
```

A FastAPI TestClient requests public pages and their referenced first-party
`/studio-assets/` CSS/JS, reporting which files are loaded by which page,
the byte size of each original response, total unique public assets, and
broken asset URLs. The safety thresholds are deliberately generous:
700,000 bytes per file and 3,000,000 bytes across unique assets. They are
*regression guards*, not proven speed targets.

### C. Always-on GitHub Actions validation

New workflow: `.github/workflows/public_browser_quality.yml`. It runs
for PRs targeting `feat/founders-omni-editorial-20261116` when public
files change, for pushes to that branch, and manually. It installs Python
3.12, Ruff, pytest, Chromium, migrates a throwaway SQLite test DB, starts
FastAPI on loopback and performs the two audits.

The `omnifactory-public-quality` GitHub Actions artifact contains both
reports and the real captured public screenshots. No secrets and no private
pages are intentionally visited. On failure, the workflow prints the last
lines of the development server log.

## Security and interpretation

- Browser URL is **restricted to http://127.0.0.1 or localhost with port**.
- No URL, credentials, data or screenshots are uploaded outside the selected
  CI artifact; no customer account is logged in.
- The workflow's ephemeral SQLite database is not a production Neon DB.
- Screenshots capture *public test/demonstration pages only*.
- Fonts and other third-party resources may load during real-page rendering;
  scripts do not send custom telemetry or customer events to them.
- Local Chromium timing, response sizes, layout geometry and asset inventory
  do **not** establish production LCP/INP/CLS, ranking or visitor conversions.
  Gather real browser Core Web Vitals on the deployed URL separately.

## Local Windows acceptance

```powershell
python -m ruff check .
python -m pytest -q tests/test_public_qa_contract.py
python -m pytest -q
python -m scripts.public_asset_budget
```

For the Chromium stage, start the app separately and run the command above.
Review the report and screenshots at phone and desktop widths. Do not merge
on a red GitHub check. If the screenshot differences are due to the browser
or fonts, document the variance; don't disable the quality gate silently.

## No invented optimization claims

This release installs the baseline and catches regressions. After obtaining
the first real artifact, prioritize repairing failures and reducing measured
public asset duplication, long critical render paths and mobile overflow,
then re-run the same gate to prove the difference.
