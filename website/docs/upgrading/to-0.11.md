---
title: Upgrading to 0.11
---

This update brings these headline features:

- Add Backup and Restore, currently only externally schedulable, documented [here](../maintenance/backups/index.md)
- New Admin Dashboard with more metrics and Charts

  Shows successful and failed logins from the last 24 hours, as well as the most used applications
- Add search to all table views
- Outpost now supports a Docker Controller, which installs the Outpost on the same host as passbook, updates and manages it
- Add Token Identifier

  Tokens now have an identifier which is used to reference to them, so the Primary key is not shown in URLs
- `core/applications/list` API now shows applications the user has access to via policies

## Upgrading

This upgrade can be done as with minor upgrades, the only external change is the new docker-compose file, which enabled the Docker Integration for Outposts. To use this feature, please download the latest docker-compose from [here](https://raw.githubusercontent.com/BeryJu/passbook/master/docker-compose.yml).

Afterwards, you can simply run `docker-compose up -d` and then the normal upgrade command of `docker-compose run --rm server migrate`.
