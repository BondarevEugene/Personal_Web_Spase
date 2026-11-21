# OMNIFACTORY Visual Excellence / Corporate Public Homepage

## Problem addressed

The public homepage had a sidebar mixing local anchors with outbound
navigation, including two duplicate trust links. At smaller screen sizes
the three calls to action and long lists of engineering tools crowded the
first screen.

## Visual and UX changes

- **Focused first screen** retains the original source-authored hero title,
  lead paragraph and the functional Graph Studio / dashboard architecture
  graphic. This is required by the existing Creative Content Studio's
  guarded original-to-edited text substitution.
- Added an explicit three-path choice for users:
  - **Build:** /services, actual services and project scope.
  - **Verify:** /cases, real first-party code and case descriptions.
  - **Explore:** /demo, read-only Experience Lab.
- A restrained horizontal proof strip communicates real principles:
  own Python engineering, verifiable scenarios and clearly described limits.
  No fake client counts, revenue or awards.
- Sidebar now contains **six distinct in-page anchors** only:
  overview, tools, calculator, journal, founders, system status.
  External product sections are linked from the primary page content and
  header rather than mixed into the internal table of contents.
- Responsive visual improvements: tighter mobile hero typography, coherent
  high-intent links, platform schematic, real contact CTA pinned on narrow
  phones, iOS/Android safe-area support, keyboard focus and reduced motion.
- Lightweight geometric treatment uses CSS only: no extra images, SVG file
  downloads, JavaScript bundles, tracking or third-party UI frameworks.
- Preconnects to the existing Google Fonts origins before site.css
  references those same fonts. This does not add a new font dependency.

## Safety boundaries

- Original homepage hero H1 and intro are unchanged, preserving
  `omni_site.creative_store.render_home_hero`.
- The new mobile CTA points to the existing real Studio inquiry form.
- Authenticated account, operator, CRM, payments and generated images
  are entirely unaffected.
- No new database schema or Alembic migration.
- The CSS does not claim an actual Core Web Vitals measurement. Real
  performance must be measured on the deployed website.
- Schematic placeholders remain placeholders until approved real
  product screenshots are available.

## Acceptance checklist

```powershell
python -m ruff check .
python -m pytest -q tests/test_public_visual_excellence.py
python -m pytest -q
```

Browser smoke tests:
1. On 320, 360, 375, 430, 768, 1024 and desktop widths, open homepage
   without sideways scroll and test all three first-screen paths.
2. At mobile width, test bottom contact CTA with on-screen browser bars
   and device gesture safe area, especially Android.
3. Try Tab/Enter focus, reduced-motion settings, and visible menu close.
4. Check the calculator, existing graph, Experience Lab, service pages,
   case library, trust center, status and Client Workspace login.
5. As an operator, publish and restore homepage H1 text using Creative
   Content Studio and verify styling and remaining links.
6. Run Chrome/Firefox Lighthouse / PageSpeed on the actual deployed URL
   and compare LCP, INP, CLS and transfer bytes against an earlier baseline.

## Further performance decisions

The homepage currently loads several distinct CSS files because each
past feature layer owns a scoped surface. This patch does not combine
them blindly: first capture a real browser waterfall and coverage report.
Then bundle only proven critical style groups, preserving styles order.
No performance improvement percentage is claimed before that verification.
