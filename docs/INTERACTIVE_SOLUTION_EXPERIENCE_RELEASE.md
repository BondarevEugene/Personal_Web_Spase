# OMNIFACTORY · Experience Lab / Interactive Solution Journeys

## Release purpose

Give potential clients a high-design, interactive way to understand how
a business problem becomes a technical scenario, implementation and
verified result. This is a **read-only architectural visualization**, not
a runtime simulator. No customer data or integrations are triggered.

## Public navigation

- `/demo` — full Experience Lab with all three illustrated business journeys.
- `/demo/crm` — client request → project → milestones → acceptance.
- `/demo/telegram` — Telegram product choice → materials → validation →
  generation → delivery.
- `/demo/automation` — trigger → conditions → actions → dry-run → control.
- Homepage `/` links to the lab and to each deep link. The public
  `/sitemap.xml` includes the new pages only with an explicitly configured
  HTTPS `OMNI_PUBLIC_BASE_URL`.

## Corporate design contract

- Graphite-dark foundation with structured grid; editorial type and
  controlled violet/cyan/mint differentiation between scenarios.
- Five schematic nodes per journey with **real technical labels and
  grounded explanations** based on first-party project modules.
- Accessible tabs, node-selection buttons, inspector, previous/next
  navigation, progress indication and permanent scenario links.
- Keyboard access, focus-visible outlines, mobile reflow and reduced-motion
  support. Script is dependency-free and small.
- The existing case-library image placeholders remain in place. Experience Lab
  contains abstract CSS/HTML architecture visualization, **not fabricated
  screenshots**.

## Important truth boundaries

This screen explicitly distinguishes conceptual flows from live operations:

- It does **not** execute external APIs, generate a Telegram bot, create an
  order, send messages, run billing, process real photos or perform AI work.
- The case and service links direct visitors to actual corresponding
  platform routes, including the private client workspace where login may
  be required.
- Food_Porn production payment and video capabilities are not asserted.
- A workflow dry-run cannot certify all third-party integrations.
- In-browser selection does not call APIs, write local storage, collect
  visitor identities or generate analytics events.

## Test / acceptance checklist

```powershell
python -m ruff check .
python -m pytest -q tests/test_public_solution_experience.py
python -m pytest -q
```

Manual checks:

1. Open `/` → Experience Lab → select CRM, Telegram and Automation.
2. For each, use nodes and Previous/Next; the correct explanation, node
   highlight, count and progress value must update.
3. Test direct `/demo/telegram` load, browser refresh, and other deep links.
4. Navigate with Tab/Enter/Space; verify focus, disable first/last step
   buttons, and test narrow Android viewport without horizontal scrolling.
5. Verify that technical facts and limitations correspond to code, case pages
   and docs. Watch the Network panel: user interactions should not issue
   new requests.
6. Verify homepage, sitemap and real lead CTA `/studio#contact`.

No schema migration, new credentials, client account changes or payment
integration in this release.
