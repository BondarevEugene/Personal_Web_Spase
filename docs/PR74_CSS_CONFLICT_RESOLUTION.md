# PR #74 conflict resolution / consolidated public CSS

The original PR #74 was authored against an older homepage state. PR #76
has since landed on the founders editorial branch and its generated CSS
pipeline uses `scripts/build_home_css.py` and
`home_features.bundle.css`. Blindly copying PR #74's
`home.bundle.css` and `scripts/build_public_styles.py` would replace
newer work and break the Blueprint Studio regression checks.

## Preserved implementation

- `site.css` remains the foundational stylesheet.
- Nine feature stylesheets are bundled in their original cascade order
  by `scripts.build_home_css` and loaded as one feature request.
- Homepage therefore loads **two** local CSS requests, not the ten
  independent stylesheets targeted by the original performance work.
- The existing `--check` verifies the committed bundle byte-for-byte.
- Blueprint Studio, Chromium's 40 route/viewport checks, and the
  established public quality workflow remain in place.

## Verification

```powershell
python -m scripts.build_home_css --check
python -m ruff check tests/test_public_css_merge_contract.py
python -m pytest -q tests/test_public_css_merge_contract.py tests/test_public_home_css_bundle.py tests/test_public_blueprint_studio.py
python -m pytest -q
```

Do not merge the outdated PR #74 after this change. This reconciliation
preserves the current production implementation rather than claiming an
unmeasured speed improvement or overwriting newer assets.
