---
title: Backup and restore your authentik instance
sidebar_label: Backup & Restore
---

This guide outlines the critical components to back up and restore in authentik.

## PostgreSQL database

The PostgreSQL database is the most important part of an authentik backup. Without it, authentik cannot be restored to a usable state.

### Backup

- Stores all persistent authentik data, including users, policies, flows, and configuration.
- Loss of this database means full application data loss.
- Use PostgreSQL-native tooling such as [`pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html), [`pg_dumpall`](https://www.postgresql.org/docs/current/app-pg-dumpall.html), or [continuous archiving](https://www.postgresql.org/docs/current/continuous-archiving.html).
- Exclude the PostgreSQL system databases `template0` and `template1`.
- Keep backups somewhere other than the database host when possible.

### Restore

- Restore the PostgreSQL database before bringing authentik back into service.
- Use PostgreSQL-native restore tooling such as [`pg_restore`](https://www.postgresql.org/docs/current/app-pgrestore.html) or `psql`, depending on how the backup was created.
- Verify that the restored database is complete before reconnecting authentik.

For deployment-specific PostgreSQL upgrade runbooks, see:

- [Upgrade PostgreSQL on Docker Compose](../../troubleshooting/postgres/upgrade_docker.md)
- [Upgrading PostgreSQL on Kubernetes](../../troubleshooting/postgres/upgrade_kubernetes.md)

For PostgreSQL connection settings, TLS, replicas, and pooler compatibility, see the [PostgreSQL configuration reference](../../install-config/configuration/configuration.mdx#postgresql-settings).

## Static directories

These directories are mounted as volumes in containerized installations and must be restored if they were part of the backup to maintain authentik’s expected functionality.

| Directory               | Purpose                                                                      | Backup and Restore Notes                                                                                                                                                             |
| ----------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **`/data`**             | Stores application icons, flow backgrounds, uploaded files, and CSV reports. | Only required if not using S3 external storage. External storage should be backed up using the [AWS S3 Sync](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html) utility. |
| **`/certs`**            | Stores TLS certificates in the filesystem.                                   | Backup if you rely on these certificates present in the filesystem. Not needed if authentik has already imported them, as certificates are stored in the database.                   |
| **`/custom-templates`** | Stores custom changes to the authentik UI.                                   | Required if you modified authentik's default appearance.                                                                                                                             |
| **`/blueprints`**       | Stores blueprints.                                                           | Optional but recommended if using custom blueprints.                                                                                                                                 |
