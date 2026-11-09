# OmniFactory • Studio ↔ Platform, phase 1

## Scope
- `/studio`: the public Studio v3 site. The existing HTML design and content remain unchanged except for a small link to the platform in the header and footer.
- `/`: the existing OmniFactory platform landing page, now linking back to Studio and to its **existing** visual builder page.
- `/builder_pro_final.html`: legacy visual-builder interface. The route already existed; no runtime or permissions have been added in this phase.
- `/studio/api/lead`: newly connected existing Telegram lead router. The form submits server-side and requires `OMNI_STUDIO_BOT_TOKEN` and `OMNI_STUDIO_CHAT_ID` from the environment. Without credentials it returns HTTP 503; no false success is shown.

## Local checks
```powershell
python -m pip install pytest
python -m pytest -q tests/test_studio_platform_phase1.py
python run.py
```

Open `http://127.0.0.1:8000/studio` and follow **Платформа** to `/`. In the platform sidebar, use **ВИЗУАЛЬНЫЙ КОНСТРУКТОР** to open the legacy Drawflow UI.

## Security boundary / not completed
- The platform, legacy builder, dashboard and admin routes currently do not have a confirmed production-grade customer authentication boundary. They MUST NOT be described or exposed as a secure private customer cabinet in production until authentication, authorization and tenant isolation are implemented.
- The legacy builder interface references backend API endpoints not mounted by `server.py`. This PR restores route discovery only. Bot compilation, saving, deployment and CRM syncing are **not** claimed to work.
- The lead endpoint's in-process IP throttle is basic and is not a distributed production anti-abuse control.
- A separate security PR handles the published Firebase service-account JSON. **Rotate/revoke the exposed key** and plan history cleanup; this PR does not remediate historic exposure.
- Git history contains tracked virtual environments and oversized compiled binaries; clean them in a separate, carefully scoped operation.

## Next engineering phase
Inventory and normalize builder graph schemas and API routes, implement server-side validation and secure per-user project persistence, then integrate tenant-scoped CRM events through authenticated APIs. Keep `/studio` independent of CRM/admin privileges.
