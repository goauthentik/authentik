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

### Task retries

When a task throws an exception, the worker will automatically try to re-run the task up to [`AUTHENTIK_WORKER__TASK_MAX_RETRIES`](../../install-config/configuration/configuration.mdx#authentik_worker__task_max_retries) times. Those retries are done with an exponential backoff. Only after all retries are exhausted is the task marked as failed. Otherwise, it stays in the "Running" status while the worker retries it. However, logs shown in the admin interface are updated after each try.

### Time limits

All tasks have a time limit. If running a task takes longer than than limit, the task is cancelled and marked as failed. The default time limit is configurable with [`AUTHENTIK_WORKER__TASK_DEFAULT_TIME_LIMIT`](../../install-config/configuration/configuration.mdx#authentik_worker__task_default_time_limit). Some tasks override that time limit for specific purposes, like synchronization.

## Manage the worker

### Scaling

How many workers are needed will depend on what tasks are expected to run. The number of tasks that can concurrently run is workers replicas (1 for docker-compose, defaults to 1 for the Helm chart but can be configured) multiplied by [`AUTHENTIK_WORKER__PROCESSES`](../../install-config/configuration/configuration.mdx#authentik_worker__processes) multiplied by [`AUTHENTIK_WORKER__THREADS`](../../install-config/configuration/configuration.mdx#authentik_worker__threads).

For example, let's say an LDAP source is configured with 1000 users and 200 groups. The LDAP source syncs the users first, then the groups, then memberships and finally deletes extra users in authentik if that option is turned on. All those steps are done by splitting the objects to synchronize into pages, of size [`AUTHENTIK_LDAP__PAGE_SIZE`](../../install-config/configuration/configuration.mdx#authentik_ldap__page_size). Let's say that setting is 50. That means there are `1000 / 50 = 20` pages of users, `200 / 50 = 4` pages of groups. We won't worry about the number of membership and deletion pages, because those are usually smaller than the previous ones.

This means that the maximum number of concurrent tasks will be 20, plus 1 as there is a "meta" task watching over the synchronization and managing the steps so they are executed in order. Thus, for the synchronization to run as fast as possible, there needs to be 21 available workers when it starts. However, other tasks might also be running at the same time, or might get created while the synchronization is running. Thus, we recommend having more workers than necessary to keep a buffer for those tasks.

### Monitor worker and tasks status

The workers expose metrics about their operation on [`AUTHENTIK_LISTEN__METRICS`](../../install-config/configuration/configuration.mdx#authentik_listen__metrics). Those metrics allow monitoring of the number of pending, failed and successful tasks. They also provide insights about tasks durations.

The worker also has an available healthcheck endpoint. See [Monitoring](./monitoring.md#worker-monitoring) for details.
