# Telegram Runtime · persistent state

Runtime can use a SQLite database on **persistent storage**:

```powershell
$env:OMNI_STATE_SQLITE_PATH = "C:\\omni-data\\telegram-state.db"
```

- Stores conversation cursor and variables per (chat_id, user_id).
- Rejects duplicate Telegram update IDs, including after a process restart.
- Rejected updates are acknowledged without re-running handlers.
- On handler failure the update ID is released for retry. Telegram delivery is **not exactly once**: if a handler sent a message before failing, retries may send it again.
- WAL mode is used. The SQLite file must be on a durable mounted volume; ephemeral container files are not persistent.
- **Single replica only.** No distributed coordination, lease or horizontal scaling.
- `/health` reports `persistent_state`, but does not claim verified Telegram delivery.
- Periodic pruning can be performed via `DialogueStore.prune()` from an operator maintenance task. Do not prune active dialogues without considering the retention policy.
- This release does not enable Railway provisioning, Telegram webhook registration, restart controls or provider billing.
