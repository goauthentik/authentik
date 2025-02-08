---
title: Backup authentik
---

This guide provides steps to back up authentik, including its PostgreSQL database, Redis data, and some important directories. These instructions cover both Kubernetes and Docker environments.

## PostgreSQL Database Backup

### Dump the PostgreSQL Database

Run the following command using Docker or Kubernetes to create a backup of all databases, excluding system ones:

**Docker:**

```sh
docker exec authentik-postgresql su - postgres -c "pg_dumpall --clean --file /var/lib/postgresql/backup.sql --verbose --exclude-database=postgres --exclude-database=template0 --exclude-database=template1"
```

**Kubernetes:**

```sh
kubectl exec -it authentik-postgresql -n authentik -- su - postgres -c "pg_dumpall --clean --file /var/lib/postgresql/backup.sql --verbose --exclude-database=postgres --exclude-database=template0 --exclude-database=template1"
```

### Moving the Backup to Your Host System

If you want to move the backup file from the container to your host system, use the following commands:

**Docker:**

```sh
docker cp authentik-postgresql:/var/lib/postgresql/backup.sql ./backup.sql
```

**Kubernetes:**

```sh
kubectl cp authentik-postgresql:/var/lib/postgresql/backup.sql ./backup.sql -n authentik
```

## Redis Backup

Redis data can be dumped using:

**Docker:**

```sh
docker exec authentik-redis redis-cli save
```

**Kubernetes:**

```sh
kubectl exec -it authentik-redis -n authentik -- redis-cli save
```

This saves the Redis dump to `/data/dump.rdb`.

### Moving the Backup to Your Host System

If you want to move the backup file from the container to your host system, use the following commands:

**Docker:**

```sh
docker cp authentik-redis:/data/dump.rdb ./dump.rdb
```

**Kubernetes:**

```sh
kubectl cp authentik-redis:/data/dump.rdb ./dump.rdb -n authentik
```

## Important Directories to Back Up

The following directories are mounted automatically in the **Docker Compose** and **Kubernetes manifests**, so ensure they are backed up:

- **`/media`**: Stores icons, flow backgrounds, and other media files (if not using S3 or external URLs).
- **`/certs`**: Contains only externally provided certificates.
- **`/custom-templates`**: Stores custom templates.
- **`/blueprints`**: Optional directory for blueprints.
