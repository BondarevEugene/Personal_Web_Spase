# OMNIFACTORY Graph Studio — Release Acceptance Gate

This is a **Telegram/aiogram 3 exporter**, not a general-purpose n8n runtime.

## Automated acceptance (must be green)

Run from the repository root in Python 3.12 environment:

```powershell
.\.venv-omni\Scripts\python.exe -m pytest -q tests/test_simple_builder.py tests/test_builder_export_acceptance.py tests/test_graph_diagnostics.py tests/test_graph_history.py tests/test_graph_auto_layout.py tests/test_graph_step_debugger.py tests/test_graph_groups.py tests/test_builder_projects.py
.\.venv-omni\Scripts\python.exe -m pytest -q
.\.venv-omni\Scripts\python.exe -m ruff check .
```

Do not merge when CI fails. The acceptance tests import **bot.py from the ZIP** and call
real exported handlers with a mocked Telegram transport; they do not send messages.

## Manual browser gate

1. Open `/architect` on desktop and narrow mobile viewport. Check compact graphite UI, keyboard tab order, distinct type colors, no horizontal page overflow.
2. Create scenario with a message, a choice (two different destinations), input, set-variable, condition, end and a media node. Fill all required fields.
3. Move nodes, connect them, group them, rename a group, undo/redo, auto-layout, save to account.
4. Reload the browser; open saved project and verify graph positions, links, groups and selected start node.
5. Run diagnostics and check errors; repair all blocking issues.
6. Simulate both choice paths, input and condition. Compare step-by-step snapshots with messages.
7. Export ZIP, extract it into a **clean temporary folder**, create Python venv, install requirements and start bot.py with a **separate test BotFather token**.
8. In Telegram, /start and test both branches, invalid input and repeated tapping of an old button. Restart exported bot and ensure in-memory sessions are clearly reset.
9. Verify two different customers cannot read/update/delete each other's saved projects (backend owner-scoped + CSRF).
10. Verify no bot token or account cookie appears in scenario.json, code or logs.

## Known boundaries — do not misrepresent these as finished

- The exported dialogue cursor and variable store are **process-memory only**. Restart resets conversation state.
- Cloud provisioning, runtime monitoring of exported bots, OAuth integrations, arbitrary Python execution and production Telegram webhook setup are separate capabilities.
- Grouping currently organizes navigation; it does not create subgraph execution semantics.
- URL media must be accessible to Telegram; no upload/storage engine is bundled in the ZIP.

**Release criterion:** a customer can independently build, save, validate, test,
export, install and run a standard aiogram 3 conversation. Do not claim
production-grade universal automation until integration/runtime capabilities exist.
