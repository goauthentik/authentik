---
title: Restore authentik
---

This guide outlines the critical components to restore authentik.

## PostgreSQL database

- **Role:** Stores all persistent data (users, policies, configurations, etc.).
- **Restoration Importance:** Essential for full recovery; authentik will not function without it.
- **Restoration Guidance:**
    - Use PostgreSQL’s official restore commands (e.g., [`pg_restore`](https://www.postgresql.org/docs/current/app-pgrestore.html)) to restore backups.

## Redis database

- **Role:** Manages temporary data:
    - User sessions (users must reauthenticate after restoration).
    - Reputation scores (restored from PostgreSQL if saved).
    - Pending tasks (not recoverable if lost).
- **Restoration Importance:** Service impact but no permanent data loss.
- **Restoration Guidance:**
    - Follow Redis’ official documentation to import your backup by restoring an RDB file using the provided guidelines in the [Import Data into Redis](https://redis.io/learn/guides/import#restore-an-rdb-file) guide.

## Static directories

These directories must be restored if they were part of the backup to maintain authentik’s expected functionality.

| Directory               | Purpose                                                         | Restoration Notes                                               |
| ----------------------- | --------------------------------------------------------------- | --------------------------------------------------------------- |
| **`/media`**            | Stores application icons, flow backgrounds, and uploaded files. | Restore if not using external storage (e.g., S3).               |
| **`/certs`**            | Custom TLS certificates (if provided externally).               | Restore if you previously added custom certs in this directory. |
| **`/custom-templates`** | Custom branch templates.                                        | Required if you modified authentik’s default appearance.        |
| **`/blueprints`**       | Stores blueprints.                                              | Recommended if using custom blueprints.                         |
