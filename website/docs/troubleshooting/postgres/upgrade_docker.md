---
title: Upgrade PostgreSQL on Docker Compose
---

### Dump your database

Dump your existing database with `docker compose exec postgresql pg_dump -U authentik -d authentik -cC > upgrade_backup_12.sql`.

Before continuing, ensure the SQL dump file (`upgrade_backup_12.sql`) includes all your database content.

### Stop your authentik stack

Stop all services with `docker compose down`.

### Backup your existing database

If you use Docker volumes you can run the following command: `docker volume create authentik_database_backup && docker run --rm -v authentik_database:/from -v authentik_database_backup:/to alpine sh -c 'cd /from && cp -a . /to'`. You can find the name of the `authentik_database` volume with `docker volume ls`.

If your data is a file path: `cp -a /path/to/v12-data /path/to/v12-backup`

### Delete your old database

:::::danger
Do not execute this step without checking that the backup (previous step) completed successfully.
:::::

If you use Docker volumes: `docker volume rm -f authentik_database`.

If your data is a file path: `rm -rf /path/to/v12-data`

### Modify your docker-compose.yml file

Update the PostgreSQL service image from `docker.io/library/postgres:12-alpine` to `docker.io/library/postgres:16-alpine`.

Add `network_mode: none` to prevent connections being established to the database during the upgrade.

### Recreate the database container

Pull new images and re-create the PostgreSQL container: `docker compose pull && docker compose up --force-recreate -d postgresql`

Apply your backup to the new database: `cat upgrade_backup_12.sql | docker compose exec -T postgresql psql -U authentik`

Remove the network configuration setting `network_mode: none` that you added to the Compose file in the previous step.

### Recreate authentik

Start authentik again: `docker compose up --force-recreate -d`
