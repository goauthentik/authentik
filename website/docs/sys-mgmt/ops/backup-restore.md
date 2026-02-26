---
title: Backup and restore your authentik instance
sidebar_label: Backup & Restore
---

This guide outlines the critical components to back up and restore in authentik.

## PostgreSQL database

### Backup

- **Role:** Stores all persistent data (users, policies, configurations, etc.).
- **Impact of Loss:** Complete data loss, requiring full restoration to recover functionality.
- **Backup Guidance:**
    - Use PostgreSQL's native tools ([`pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html), [`pg_dumpall`](https://www.postgresql.org/docs/current/app-pg-dumpall.html), or [continuous archiving](https://www.postgresql.org/docs/current/continuous-archiving.html)).
    - Exclude system databases: `template0` and `template1`.
- **Official Documentation:** [PostgreSQL Backup and Restore](https://www.postgresql.org/docs/current/backup.html)

### Restore

- **Restoration Importance:** Essential for full recovery; authentik will not function without it.
- **Restoration Guidance:**
    - Use PostgreSQL's [`pg_restore`](https://www.postgresql.org/docs/current/app-pgrestore.html) or other official methods.

## Static directories

These directories are mounted as volumes in containerized installations and must be restored if they were part of the backup to maintain authentik’s expected functionality.

| Directory               | Purpose                                                                      | Backup and Restore Notes                                                                                                                                                             |
| ----------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **`/data`**             | Stores application icons, flow backgrounds, uploaded files, and CSV reports. | Only required if not using S3 external storage. External storage should be backed up using the [AWS S3 Sync](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html) utility. |
| **`/certs`**            | Stores TLS certificates in the filesystem.                                   | Backup if you rely on these certificates present in the filesystem. Not needed if authentik has already imported them, as certificates are stored in the database.                   |
| **`/custom-templates`** | Stores custom changes to the authentik UI.                                   | Required if you modified authentik's default appearance.                                                                                                                             |
| **`/blueprints`**       | Stores blueprints.                                                           | Optional but recommended if using custom blueprints.                                                                                                                                 |
