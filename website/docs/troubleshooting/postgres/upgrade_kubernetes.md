---
title: Upgrade PostgreSQL on Kubernetes
---

## Preparation

-   `authentik-postgresql-0` is the Kubernetes Pod running PostgreSQL.

### Prerequisites

This migration requires some downtime, during which authentik must be stopped. To do this, run the following command:

```shell
kubectl scale deploy --replicas 0 authentik-server
kubectl scale deploy --replicas 0 authentik-worker
```

### Dump the current database

Run `kubectl exec -it authentik-postgresql-0 -- bash` to get a shell in the PostgreSQL pod.

Run the following commands to dump the current data into a `.sql` file:

```shell
# This is the path where the PVC is mounted, so we'll place the dump here too
cd /bitnami/postgresql/
# Set the postgres password based on the `POSTGRES_POSTGRES_PASSWORD` environment variable
export PGPASSWORD=$POSTGRES_POSTGRES_PASSWORD
# Dump the authentik database into an sql file
pg_dump -U postgres $POSTGRES_DB > dump-11.sql
```

### Stop PostgreSQL and start the upgrade

To upgrade, change the following entries in your `values.yaml` used to deploy authentik:

```yaml
postgresql:
    diagnosticMode:
        enabled: true
    image:
        tag: 15.2.0-debian-11-r26
```

Now run `helm upgrade --install authentik authentik/authentik -f values.yaml` to apply these changes. Depending on your configuration, you might have to repeat the steps from [Prerequisites](#prerequisites).

After the upgrade is finished, you should have a new PostgreSQL pod running with the updated image.

### Remove the old data

Because the PVC mounted by the PostgreSQL pod still contains the old data, we need to remove/rename that data, so that PostgreSQL can initialize it with the new version.

Run `kubectl exec -it authentik-postgresql-0 -- bash` to get a shell in the PostgreSQL pod.

Run the following commands to move the old data:

```shell
# This is the path where the PVC is mounted
cd /bitnami/postgresql/
# Move Postgres' data folder to data-11, which is the version we're upgrading to.
# The data folder can also be deleted; however it is recommended to rename it first
# in case the upgrade fails.
mv data data-11
```

### Restart PostgreSQL

In the step [Stop PostgreSQL and start the upgrade](#stop-postgresql-and-start-the-upgrade), we enabled the _diagnostic mode_, which means the PostgreSQL pod is running, but the actual Postgres process isn't running. Now that we've removed the old data directory, we can disable the diagnostic mode.

Once again, change the following entries in your `values.yaml` used to deploy authentik:

```yaml
postgresql:
    image:
        tag: 15.2.0-debian-11-r26
```

And once again run `helm upgrade --install authentik authentik/authentik -f values.yaml` to apply these changes. Depending on your configuration, you might have to repeat the steps from [Prerequisites](#prerequisites).

After the PostgreSQL pod is running again, we need to restore the data from the dump we created above.

Run `kubectl exec -it authentik-postgresql-0 -- bash` to get a shell in the PostgreSQL pod.

Run the following commands to restore the data:

```shell
# This is the path where the PVC is mounted
cd /bitnami/postgresql/
# Set the Postgres password based on the `POSTGRES_POSTGRES_PASSWORD` environment variable.
export PGPASSWORD=$POSTGRES_POSTGRES_PASSWORD
psql -U postgres $POSTGRES_DB < dump-11.sql
```

After the last command finishes, all of the data is restored, and you can restart authentik.

### Restarting authentik

Run `helm upgrade --install authentik authentik/authentik -f values.yaml` once again, which will restart your authentik server and worker containers.
