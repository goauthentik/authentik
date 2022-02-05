---
title: Release 2022.2
slug: "2022.2"
---

## Breaking changes

### Removal of integrated backup

The integrated backup functionality has been removed due to the following reasons:

- It caused a lot of issues during restore, with things breaking and difficult to restore backups
- Limited compatibility (only supported local and S3 backups)
- Most environments already have a solution for backups, so we feel that investing more time into making this feature better should be spent on more important things.

If you don't already have a standard backup solution for other applications, you can consider these replacements:

- https://github.com/kartoza/docker-pg-backup for docker-compose and
- https://devtron.ai/blog/creating-a-kubernetes-cron-job-to-backup-postgres-db/ or https://cwienczek.com/2020/06/simple-backup-of-postgres-database-in-kubernetes/ for Kubernetes


## Upgrading

This release does not introduce any new requirements.

### docker-compose

Download the docker-compose file for 2022.2 from [here](https://goauthentik.io/version/2022.2/docker-compose.yml). Afterwards, simply run `docker-compose up -d`.

The previous backup directory will persist, and can still be used with other tools.

### Kubernetes

Update your values to use the new images:

```yaml
image:
  repository: ghcr.io/goauthentik/server
  tag: 2022.2.1
```

Backup-related settings can be removed but will not cause any errors either.
