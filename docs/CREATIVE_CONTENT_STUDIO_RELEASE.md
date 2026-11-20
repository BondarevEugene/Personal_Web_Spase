# OMNIFACTORY — Creative Content Studio / Enterprise Art Direction

## One coherent brand, with stronger creative expression

This release extends the operator's CMS to the **public homepage hero**, all
three service detail and directory entries, and all four first-party project
cases. Each page remains grounded in the verified product catalogue and its
own source repository. The visual system is sharper, but it **does not add
fictional product screenshots, client logos, awards, or performance numbers**.

### Editorial design principles

- **One brand**: consistent graphite/near-black base, precise technical grids,
  controlled violet accent, per-product mint/cyan secondary highlights.
- **Clear hierarchy**: one large editorial statement per page, then technical
  evidence, deliverables, trade-offs and an honest CTA.
- **Creative geometry**: CSS-only circular and grid compositions; no heavy
  animation or additional image downloads.
- **Mobile-first**: readable text, reflowed cards and accessible keyboard
  focus. Reduced-motion rules for creative surfaces.
- **Transparency**: existing schematic placeholders stay intentionally
  schematic until real, approved screenshots are available.

## Operator workflow

Open `/support/creative` from the operator desk or editorial dashboard.
Only immutable UUIDs in `OMNI_SUPPORT_OPERATOR_IDS` can access it; the
ordinary customer role never grants editorial permissions.

1. Pick homepage hero, one of three services, or one of four product cases.
2. Edit a headline (12-180 characters) and product promise (40-800 characters).
3. **Save draft**. It is not rendered on public pages.
4. Check the visual preview and verify technical claims.
5. **Publish immediately** or specify a future UTC date/time. For scheduled
   publication, the previous live version remains visible until the date.
   On/after the specified time, the queued text appears on public requests.
   No scheduler or background job is required.
6. **Restore source** removes both current and scheduled public overrides.
   The checked-in original remains unchanged in Git.

The source repo URL, product links, slug, scope, limitations, tech stack,
workflow, and current legal/security notices are immutable in this release.
Homepage edits replace only the checked-in H1 and first product paragraph
using exact-match guarded substitution and HTML escaping. The original
HTML/CSS/JS design and conversion buttons remain intact.

The special separator `|` in the homepage title divides the first plain
line and the violet-accented second line. Example:
`Процессы под контролем. | Инженерное будущее начинается здесь.`
If omitted, the entire title renders as a single escaped accent line.

The editor uses UTC input for scheduled publication. Operators should check
timezones before entering the intended publication time. This is a **view-time
scheduled release**, not a queued email or social post.

## Persistence and deployment

Alembic `20261120_portal_17` adds
`portal_public_page_revisions`, with separate draft, live, and scheduled
text fields. The production release doctor will check that table.

```powershell
python -m alembic -c portal_alembic.ini upgrade head
python -m portal.release_doctor --production --routes --database --json
python -m ruff check .
python -m pytest -q tests/test_creative_content_studio.py
python -m pytest -q
```

For real Neon production, use the DIRECT migration URL and verify a backup
before applying schema changes. Do not merge on red CI.

## Acceptance across all public surfaces

- Check `/`, `/services`, all `/services/{slug}`, `/cases`,
  all `/cases/{slug}`, `/journal` and a journal article on desktop/mobile.
- Confirm that edited services appear in the directory and on detail pages;
  edited cases appear in gallery and detail pages; the homepage hero uses
  the brand accent line without breaking the product map.
- Check draft isolation, immediate publish, scheduled change, source rollback
  and CSRF rejection with an unauthorized customer.
- Check HTML injection is escaped; ensure product links, prices, claims,
  source references and acceptance workflows cannot be modified via CMS.
- Check accessibility, contrasts, touch targets and `prefers-reduced-motion`.

## Honesty and scope

This release does **not** add free-form CMS routing, user-uploaded imagery,
collaborative approval chains, a full historical revisions timeline, Google
Analytics OAuth, visitor tracking, or scheduled social-media distribution.
Search Console aggregate reporting remains the previous release's explicit
CSV import, and should never be portrayed as live visitor data.

Approved original client/product screenshots can replace diagram placeholders
later, after masking personally identifiable or sensitive information.
