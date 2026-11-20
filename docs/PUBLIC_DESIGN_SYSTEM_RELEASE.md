# OMNIFACTORY / Public Design System — Shell Unification

## Goal

Replace nine independently maintained public headers and footers with two
shared Jinja partials. Deliver consistent information architecture and a
usable phone-sized menu while preserving the current corporate, expressive
graphite-and-violet aesthetic, the interactive Experience Lab and real case
placeholders.

### Scope

Shared partials:
- `omni_site/templates/_public_header.html`
- `omni_site/templates/_public_footer.html`

Shared stylesheet:
- `omni_site/static/public_shell.css`

Applied to 9 page templates:
1. Service directory and service detail.
2. Case directory and case detail.
3. Trust center and trust detail.
4. Engineering journal and article.
5. Experience Lab.

All full page variants render this shell, producing one consistent menu for
all three commercial services, four cases, three trust guides, three journal
articles and three Experience Lab deep links.

### Header and footer hierarchy

Header: Platform · Services · Cases · Experience Lab · Journal · Trust ·
Discuss Project.

Footer: unified first-party engineering positioning, direct links to the
same public sections, a real Studio contact route and a return-to-main link.
This is navigation, not invented testimonials or a simulated product.

### Mobile and accessibility

- Desktop navigation has `aria-current="page"` on the active section.
- At smaller widths, a native `<details>/<summary>` menu replaces the wide
  navigation. It works with keyboard, touch and **without new JavaScript**.
- Link focus states remain visible; the menu limits viewport height and
  scrolls internally if needed.
- Reduced-motion preferences are respected.
- Non-public account/CRM/operator screens and the existing specially designed
  homepage / Studio header are intentionally **not replaced**.

### Visual consistency

One stable system for:
- near-black/graphite backgrounds,
- subtle technical borders,
- editorial typography,
- violet brand action,
- clear top-level conversion links,
- restrained mobile navigation without overloading the hero.

This release keeps all existing first-party diagrams/placeholder visuals as
placeholders. Real anonymized product screenshots can be added in a later
content approval step.

### Test and acceptance

```powershell
python -m ruff check .
python -m pytest -q tests/test_public_design_system_navigation.py
python -m pytest -q
```

On desktop and Android:
1. Open /services, /cases, /journal, /trust, /demo and a detail page in each.
2. Confirm exactly one coherent header/footer, with correct active item.
3. At 320/375/430px check menu toggle, navigation, keyboard focus, no
   horizontal scroll and no overlay truncation.
4. Confirm the main homepage and /studio keep their original product-specific
   navigation, and account/login remains unaffected.
5. Open the actual contact form via the shared CTA.
6. Check low-bandwidth and reduced-motion rendering.

No database migration, outbound analytics, user-tracking JS or payment change.
This release is a design-system and UX consolidation, not an unsupported
claim that Core Web Vitals have been measured on production.
