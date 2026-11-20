# Telegram runtime · backup and disaster recovery

## Scope and security

The SQLite file contains **conversation variables and user identifiers**. Backups contain the same sensitive data. Keep backups in encrypted storage, grant access only to operators and set an explicit retention period. Do not commit snapshots to Git, expose them through an HTTP endpoint, or send them to support chats.

The backup command uses SQLite's online backup API, so it captures a consistent snapshot while the single-replica runtime is active. The restore command is **offline only**.

## Commands

From the runtime image working directory:

```bash
python backup.py verify /data/state.db
python backup.py backup /data/state.db /data/backup-20261120.db
python backup.py verify /data/backup-20261120.db
```

Record the SHA-256 returned by the backup command in your restricted operator log.

## Restore

1. Stop the Telegram runtime and make sure no other process has opened the database.
2. Move the old `state.db`, `state.db-wal`, and `state.db-shm` files to a secure recovery directory. **Never delete them before recovery succeeds.**
3. Restore to the now-absent destination using the checksum from the backup result:

```bash
python backup.py restore /data/backup-20261120.db /data/state.db --sha256 YOUR_RECORDED_SHA256
python backup.py verify /data/state.db
```

4. Start one replica, check `/ready` and then test Telegram message delivery separately.

Restoring an older snapshot may replay Telegram update IDs processed after the backup. Treat external sends as potentially duplicated and reconcile before exposing the bot to production traffic. This is not exactly-once delivery or automatic rollback.

## Operational limitations

- Requires a persistent volume and single-replica SQLite runtime.
- The destination must not exist; the tool never overwrites a database.
- Local backups are not off-site disaster recovery until an operator securely copies them elsewhere.
- No automatic scheduling, provider provisioning or secret management is performed.
