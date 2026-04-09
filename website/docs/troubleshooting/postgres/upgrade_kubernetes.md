---
title: Upgrading PostgreSQL on Kubernetes
---

This guide walks through a manual PostgreSQL major-version upgrade for an authentik Kubernetes deployment. The process requires downtime while the database is exported, recreated, and restored.

:::info
For this guide, we assume the PostgreSQL pod is named `authentik-postgresql-0`, which is the default name in the authentik Helm chart.
:::

## Before you start

- `kubectl` access with permissions to `scale` deployments and `exec` into pods
- the `values.yaml` file used for your authentik deployment
- enough storage for a SQL dump and a copy of the old database files
- a maintenance window long enough to export and restore the database

Review [Backup and restore](../../sys-mgmt/ops/backup-restore.md) before proceeding.

## Overview

The upgrade flow is:

1. Stop authentik services
2. Back up the database
3. Prepare the data directory
4. Upgrade PostgreSQL
5. Restore database content
6. Restart authentik services

## 1. Stop authentik services

Scale down authentik so nothing accesses PostgreSQL during the upgrade:

```shell
kubectl scale deploy --replicas 0 authentik-server
kubectl scale deploy --replicas 0 authentik-worker
```

## 2. Back up the database

Connect to the PostgreSQL pod:

```shell
kubectl exec -it authentik-postgresql-0 -- bash
```

After you are connected, execute these commands to create a database backup:

```shell
# Navigate to the PostgreSQL data directory
cd /bitnami/postgresql/

# Set the PostgreSQL password from environment variable
export PGPASSWORD=$(cat $POSTGRES_PASSWORD_FILE)

# Create a full database dump
pg_dump -U $POSTGRES_USER $POSTGRES_DATABASE > /bitnami/postgresql/dump.sql
```

:::tip
Copy the dump file to a safe location outside of the pod before continuing:

```shell
# From a separate terminal
kubectl cp authentik-postgresql-0:/bitnami/postgresql/dump.sql ./authentik-db-backup.sql
```

Keeping an external copy protects you if the pod or persistent volume is recreated unexpectedly.
:::

## 3. Prepare the data directory

While still connected to the pod, prepare the data directory:

```shell
# Ensure you're in the PostgreSQL data directory
cd /bitnami/postgresql/

# Verify the SQL dump exists and has content
ls -lh dump.sql

# Preserve the existing data by renaming the directory
mv data data-old
```

:::caution
Do not delete `data-old` yet. It provides a rollback path if the restore fails.
:::

## 4. Upgrade PostgreSQL

Update `values.yaml` with the new PostgreSQL image tag:

```yaml
postgresql:
    image:
        tag: <NEW_VERSION>
```

Apply the change with Helm using your normal deployment command.

When the pod restarts with the new image, PostgreSQL initializes a new empty `data` directory because the previous one was renamed to `data-old`.

## 5. Restore database content

Connect to the PostgreSQL pod again:

```shell
kubectl exec -it authentik-postgresql-0 -- bash
```

Restore your database from the backup:

```shell
# Navigate to the PostgreSQL directory
cd /bitnami/postgresql/

# Verify your dump file is still there
ls -lh dump.sql

# Set the PostgreSQL password
export PGPASSWORD=$(cat $POSTGRES_PASSWORD_FILE)

# Import the database dump
psql -U $POSTGRES_USER $POSTGRES_DATABASE < dump.sql
```

## 6. Restart authentik services

After the restore completes successfully, scale authentik back up or re-run your Helm deployment so the server and worker return to their normal replica counts.

## 7. Verify the upgrade

After everything starts again:

- confirm the PostgreSQL pod is healthy
- check the PostgreSQL, server, and worker logs for startup or migration errors
- log in to authentik through the UI to verify the application is functioning normally

## Troubleshooting

If you encounter issues during the upgrade process:

- Check PostgreSQL logs:
    ```shell
    kubectl logs authentik-postgresql-0
    ```
- Verify the values in your `values.yaml` file match the recommended settings
- Ensure you have sufficient storage available for both the database dump and the database itself

### Dump file not found

If `dump.sql` is missing after the restart:

- You may need to restore from the external backup if you copied it out of the pod
- The volume might have been recreated if you're using ephemeral storage

### Restoring the original database

If you need to roll back to the old PostgreSQL data directory:

```shell
kubectl exec -it authentik-postgresql-0 -- bash
cd /bitnami/postgresql/
mv data data-new-failed
mv data-old data
```

Then restart PostgreSQL with the original version in your `values.yaml`.
