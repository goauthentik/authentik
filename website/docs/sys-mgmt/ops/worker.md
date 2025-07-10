---
title: Worker
slug: /worker
---

The authentik worker runs [background tasks](../background-tasks.md). It also watches for [blueprints](../../customize/blueprints/index.mdx#storage---file) and [certificates](../certificates.md#external-certificates) added to the filesystem. It runs in a separate container from the server to handle those tasks.

## How it works

authentik tasks are stored and managed using its PostgreSQL database. When authentik needs to run a background task, the following happens, inside a PostgreSQL transaction:

- a row is inserted in a dedicated PostgreSQL table, containing all the relevant information needed to run the task
- at the end of the transaction, a PostgreSQL trigger executes a `NOTIFY` command to send a notification to workers that a new task is available

The worker runs a loop to find tasks that need to run:

- it tries to `LISTEN` on the tasks channel to pick up new tasks that were just queued. It only does so for a certain period of time (configurable with [`AUTHENTIK_WORKER__CONSUMER_LISTEN_TIMEOUT`](../../install-config/configuration/configuration.mdx#authentik_worker__consumer_listen_timeout))
- if no task was received, it tries to find tasks that were not registered via a `NOTIFY` command. This happens when no worker is running when a task is created, or if the worker was busy running a task. This is done by looking into the tasks table for tasks that aren't marked as finished (either successfully or unsuccessfully). On worker start, this is done before `LISTEN`, to process older tasks first
- if a task was found or received, the worker grabs an advisory lock stating that it is responsible for the task. If several workers try to pick up the same task at the same time, only one of them will grab the task, and the others will continue without a task
- if a task was found or received and the lock was properly acquired, the task is executed
- if no task was found or the lock couldn't be acquired:
    - locks for tasks that are finished are cleaned up
    - old tasks are purged at a regular interval, configurable with [`AUTHENTIK_WORKER__TASK_PURGE_INTERVAL`](../../install-config/configuration/configuration.mdx#authentik_worker__task_purge_interval). How long tasks are kept for is configurable with [`AUTHENTIK_WORKER__TASK_EXPIRATION`](../../install-config/configuration/configuration.mdx#authentik_worker__task_expiration)
    - the scheduler is run at a regular interval, configurable with [`AUTHENTIK_WORKER__SCHEDULER_INTERVAL`](../../install-config/configuration/configuration.mdx#authentik_worker__scheduler_interval)

## Manage the worker

### Scaling

example scenario with syncing Nk users

### Tuning

explain settings

### Monitor worker and tasks status

metrics, healthcheck
