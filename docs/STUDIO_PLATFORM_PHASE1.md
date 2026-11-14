# OmniFactory • unified Studio v3 + Platform (test branch)

## Pages
- /studio — public Studio v3, preserved as the visual system reference.
- / — unified OmniFactory Platform home with the same site.css tokens, header, fonts and visual language, plus platform.css.
- /builder_pro_final.html, /architect, /builder-pro — working **simple** block editor with the same visual language. Legacy V5 HTML is preserved at templates/legacy_builder_pro_v5.html (not enabled).
- /dashboard — verified API health, not simulated throughput.
- /projects, /techkillers, /robotization and legacy /pages/* aliases serve existing legacy pages. Their own internal styling is not fully migrated in this phase.
- /studio/api/lead — existing form endpoint now registered. Configure OMNI_STUDIO_BOT_TOKEN and OMNI_STUDIO_CHAT_ID in environment for delivery. HTTP 503 without configuration.

## What actually works in the simple bot builder
- Add message/choice/photo/document/end blocks; select start node; configure next transitions and choice-button targets.
- Reorder cards (drag & drop); **ordering does not imply link connections**. Links are configured in the inspector.
- Client-side dialogue preview and JSON save/import to the browser; server-side validation of node identifiers, types, targets and maximum sizes.
- Generate a runnable aiogram 3 project ZIP containing bot.py, scenario.json, requirements.txt and README.md. BOT_TOKEN is supplied only at runtime via environment and is **not** accepted by the builder API.
- The exported bot can be run independently from Windows PowerShell using the README instructions. The code uses in-memory conversation cursors; they are reset after bot process restart.

## What does not work yet
- Server-side project storage, per-user accounts, tenant isolation, app-level bot deployment, background worker orchestration and CRM synchronization.
- Studio/Platform legacy admin pages are not authenticated yet and MUST NOT be published as a protected SaaS.
- The pre-existing advanced builder had references to non-existent JS objects and unregistered endpoints; those fake deploy paths have not been restored.
- Telegram photo/document upload by local file is not implemented: the generated runtime uses an HTTPS URL or Telegram file_id.

## Test in PyCharm (Windows)
Run in the repository root and the new Git branch:
    .\.venv\Scripts\python.exe -m pytest -q tests/test_studio_platform_phase1.py tests/test_platform_routes.py tests/test_simple_builder.py
    .\.venv\Scripts\python.exe run.py

Then open http://127.0.0.1:8000/ and click **Конструктор**.
1. Edit the starter scenario.
2. Choose **Проверить** (server must report valid nodes).
3. Choose **▶ Начать предпросмотр**; click one of the choice buttons.
4. Choose **Экспорт Python ZIP**; inspect README.md inside the downloaded file.

## Security
A service-account credential was committed in Git history. PR #16 removes that credential from current tree, but you must revoke/rotate its private key in Google Cloud IAM and coordinate historical cleanup. Never paste passwords, service-account JSON or Telegram tokens into the builder editor.
