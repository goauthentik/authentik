---
title: Upgrade PostgreSQL on Docker Compose
---

This guide walks through a manual PostgreSQL major-version upgrade for the default authentik Docker Compose deployment.

It assumes the PostgreSQL service is named `postgresql` and the authentik database is named `authentik`. If your Compose file uses different names, adjust the commands accordingly.

## Before you start

- Make sure you have enough free disk space for:
    - a SQL dump of the database
    - a copy of the existing PostgreSQL data directory or volume
    - the newly initialized PostgreSQL data directory
- Expect downtime while the database is exported, recreated, and restored.
- Review the [Backup and restore](../../sys-mgmt/ops/backup-restore.md) guidance before proceeding.

## 1. Create a logical backup

Create a database dump:

```shell
docker compose exec postgresql pg_dump -U authentik -d authentik -cC > authentik-postgres-backup.sql
```

Before continuing, confirm that `authentik-postgres-backup.sql` exists and contains the expected database objects.

## 2. Stop authentik

Stop the stack:

```shell
docker compose down
```

## 3. Back up the PostgreSQL data directory

Back up the existing PostgreSQL data before replacing it.

If you use Docker volumes:

```shell
docker volume create authentik_database_backup
docker run --rm -v authentik_database:/from -v authentik_database_backup:/to alpine sh -c 'cd /from && cp -a . /to'
```

You can find the exact name of the PostgreSQL volume with `docker volume ls` if it differs from `authentik_database`.

If your PostgreSQL data is stored on the host filesystem:

```shell
cp -a /path/to/postgres-data /path/to/postgres-data-backup
```

## 4. Remove the old data directory

:::danger
Do not continue unless both the SQL dump and the filesystem or volume backup completed successfully.
:::

If you use Docker volumes:

```shell
docker volume rm -f authentik_database
```

If your PostgreSQL data is stored on the host filesystem:

```shell
rm -rf /path/to/postgres-data
```

## 5. Update the PostgreSQL image

Edit your `compose.yml` and update the PostgreSQL image tag to the new major version.

For example, change:

```yaml
image: docker.io/library/postgres:12-alpine
```

to:

```yaml
image: docker.io/library/postgres:16-alpine
```

Temporarily add `network_mode: none` to the PostgreSQL service so nothing reconnects while you restore the dump.

## 6. Recreate PostgreSQL and restore the dump

Pull images and start only PostgreSQL:

```shell
docker compose pull
docker compose up --force-recreate -d postgresql
```

Restore the logical backup:

```shell
cat authentik-postgres-backup.sql | docker compose exec -T postgresql psql -U authentik
```

After the restore succeeds, remove the temporary `network_mode: none` setting from `compose.yml`.

## 7. Start authentik again

Start the full stack:

```shell
docker compose up --force-recreate -d
```

## 8. Verify the upgrade

After the stack is healthy again:

- confirm that authentik loads normally
- check the `server`, `worker`, and `postgresql` logs for startup or migration errors
- send a test login through the UI to confirm the application is functioning
