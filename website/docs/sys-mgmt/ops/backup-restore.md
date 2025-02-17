---
title: Backup and Restore authentik
---

This guide outlines the critical components to back up and restore in authentik.

## PostgreSQL Database

### Backup

- **Role:** Stores all persistent data (users, policies, configurations, etc.).
- **Impact of Loss:** Complete data loss, requiring full restoration to recover functionality.
- **Backup Guidance:**
    - Use PostgreSQL's native tools (`pg_dump`, `pg_dumpall`, or [continuous archiving](https://www.postgresql.org/docs/current/continuous-archiving.html)).
    - Exclude system databases: `template0` and `template1`.
- **Official Documentation:** [PostgreSQL Backup and Restore](https://www.postgresql.org/docs/current/backup.html)

### Restore

- **Restoration Importance:** Essential for full recovery; authentik will not function without it.
- **Restoration Guidance:**
    - Use PostgreSQL's [`pg_restore`](https://www.postgresql.org/docs/current/app-pgrestore.html) or other official methods.

## Redis Database

### Backup

- **Role:** Manages temporary data:
    - User sessions (lost data = users must reauthenticate).
    - Pending tasks (e.g., queued emails, outpost syncs).
- **Impact of Loss:** Service interruptions (e.g., users logged out), but no permanent data loss.
- **Backup Guidance:**
    - Use Redis' [`SAVE`](https://redis.io/commands/save) or [`BGSAVE`](https://redis.io/commands/bgsave).
- **Official Documentation:** [Redis Persistence](https://redis.io/docs/management/persistence/)

### Restore

- **Restoration Importance:** Service impact but no permanent data loss.
- **Restoration Guidance:**
    - Follow [Redis' Import Data Guide](https://redis.io/learn/guides/import#restore-an-rdb-file) to restore an RDB file.

## Static Directories

These directories are mounted as volumes in containerized installations:

| Directory               | Purpose                                  | Backup and Restore Notes                                                                                                                                                                                                                                                                            |
| ----------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`/media`**            | Icons, flow backgrounds, uploaded files. | - Only required if not using S3 external storage<br>- External storage should ideally be backed up using the [AWS S3 Sync](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html) CLI utility<br>- Restore if not using external storage                                                    |
| **`/certs`**            | Custom TLS certificates.                 | - Backup if you rely on those certificates existing on the file system<br>- authentik doesn't need them to persist after they've been imported, as certificates managed by authentik get always stored in the database<br>- Restore only if you previously relied on certificates in this directory |
| **`/custom-templates`** | Custom branch templates.                 | - Critical if you modified authentik's default appearance<br>- Required for custom UI modifications                                                                                                                                                                                                 |
| **`/blueprints`**       | Blueprints.                              | - Optional but recommended if using custom blueprints<br>- Recommended to restore blueprints                                                                                                                                                                                                        |
