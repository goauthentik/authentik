---
title: Backup authentik
---

This guide outlines the critical components to back up in authentik.

## PostgreSQL database

- **Role:** Stores all persistent data (users, policies, configurations, etc.).
- **Impact of Loss:** Complete data loss, requiring full restoration to recover authentik's functionality.
- **Backup Guidance:**
    - Use PostgreSQL's native tools (e.g., [`pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html), [`pg_dumpall`](https://www.postgresql.org/docs/current/app-pg-dumpall.html), or [continuous archiving](https://www.postgresql.org/docs/current/continuous-archiving.html)).
    - Exclude system databases (`postgres`, `template0`, `template1`).
- **Official Documentation:** [PostgreSQL Backup and Restore](https://www.postgresql.org/docs/current/backup.html)

## Redis database

- **Role:** Manages temporary data:
    - User sessions (lost data = users must reauthenticate).
    - Reputation scores (saved hourly to PostgreSQL).
    - Pending tasks (e.g., queued emails, outpost syncs).
- **Impact of Loss:** Service interruptions (e.g., users logged out, pending task loss), but no permanent data loss.
- **Backup Guidance:**
    - Use Redis' native tools (e.g., [`SAVE`](https://redis.io/commands/save) or [`BGSAVE`](https://redis.io/commands/bgsave)).
- **Official Documentation:** [Redis Persistence](https://redis.io/docs/management/persistence/)

## Static directories

These directories are mounted as volumes in containerized installations:

| Directory               | Purpose                                                         | Backup Notes                                             |
| ----------------------- | --------------------------------------------------------------- | -------------------------------------------------------- |
| **`/media`**            | Stores application icons, flow backgrounds, and uploaded files. | Only required if not using external storage (e.g., S3).  |
| **`/certs`**            | Custom TLS certificates (if provided externally).               | Backup if you manage certificates through authentik.     |
| **`/custom-templates`** | Custom branch templates                                         | Critical if you modified authentik's default appearance. |
| **`/blueprints`**       | Stores blueprints                                               | Optional but recommended if using custom blueprints.     |
