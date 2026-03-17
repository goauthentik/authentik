---
title: Upgrading PostgreSQL on Kubernetes
---

This guide walks you through upgrading PostgreSQL in your authentik Kubernetes deployment. The process requires a brief downtime period while the database is migrated.

:::info
For this guide, we assume the PostgreSQL pod is named `authentik-postgresql-0`, which is the default name in the authentik Helm chart.
:::

## Prerequisites

- `kubectl` access with permissions to `scale` deployments and `exec` into pods
- Your existing `values.yaml` file used for authentik deployment
- Basic understanding of Kubernetes and Helm commands

## Overview of workflow

The basic steps to upgrade PostgreSQL on Kubernetes are:

1. Stop authentik services
2. Back up the database
3. Prepare the data directory
4. Upgrade PostgreSQL
5. Restore database content
6. Restart authentik services

## Stop authentik services

Begin by scaling down authentik services to prevent database access during the migration:

```shell
kubectl scale deploy --replicas 0 authentik-server
kubectl scale deploy --replicas 0 authentik-worker
```

## Back up the database

Connect to your PostgreSQL pod:

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
Consider copying the dump file to a safe location outside the pod:

```shell
# From a separate terminal
kubectl cp authentik-postgresql-0:/bitnami/postgresql/dump.sql ./authentik-db-backup.sql
```

This ensures you have a backup even if something goes wrong with the pod or storage.
:::

## Prepare the data directory

While still connected to the PostgreSQL pod, prepare the data directory for the upgrade:

```shell
# Ensure you're in the PostgreSQL data directory
cd /bitnami/postgresql/

# Verify the SQL dump exists and has content
ls -lh dump.sql

# Preserve the existing data by renaming the directory
mv data data-old
```

:::caution
Do not delete the old data directory immediately. Keeping it as `data-old` allows for recovery if the upgrade encounters issues.
:::

## Upgrade PostgreSQL

Now update your `values.yaml` to specify the new PostgreSQL version:

```yaml
postgresql:
    image:
        tag: <NEW_VERSION>
```

Apply these changes using Helm to deploy the updated configuration.

This will restart the PostgreSQL pod with the new image. When the pod starts, PostgreSQL will initialize a new, empty data directory since the previous directory was renamed.

## Restore database content

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

## Restart authentik services

After the database restoration completes successfully, restart authentik using Helm with your updated configuration.

This will scale your authentik server and worker deployments back to their original replica counts.

## Troubleshooting

If you encounter issues during the upgrade process:

- Check PostgreSQL logs:
    ```shell
    kubectl logs authentik-postgresql-0
    ```
- Verify the values in your `values.yaml` file match the recommended settings
- Ensure you have sufficient storage available for both the database dump and the database itself

### Dump file not found

If your dump file is missing after upgrading:

- You may need to restore from the external backup if you copied it out of the pod
- The volume might have been recreated if you're using ephemeral storage

### Restoring the original database

For persistent problems, you can restore from the `data-old` directory if needed:

```shell
kubectl exec -it authentik-postgresql-0 -- bash
cd /bitnami/postgresql/
mv data data-new-failed
mv data-old data
```

Then restart PostgreSQL with the original version in your `values.yaml`.
