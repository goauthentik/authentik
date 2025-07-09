---
title: Background tasks
slug: /background-tasks
---

authentik uses background tasks to run various operations independently and asynchronously from the web requests it receives. Those tasks are run by the [worker](./ops/worker.md).

## What are background tasks used for?

Here is a non-exhaustive list of what background tasks are used for:

- outposts: manage [Outposts](../add-secure-apps/outposts/index.mdx) deployments, send notifications to outpost when a refresh is needed
- housekeeping: clean up old objects, check for updates, etc.
- blueprints: import and apply [Blueprints](../customize/blueprints/index.mdx)
- synchronization: sync users to and from authentik, from sources and to providers. This is used by:
    - [SCIM Provider](../add-secure-apps/providers/scim/index.md)
    - [Google Workspace Provider](../add-secure-apps/providers/gws/index.md)
    - [Microsoft Entra Provider](../add-secure-apps/providers/entra/index.md)
    - [SSF Provider](../add-secure-apps/providers/ssf/index.md)
    - [Kerberos Source](../users-sources/sources/protocols/kerberos/index.md)
    - [LDAP Source](../users-sources/sources/protocols/ldap/index.md)
- enterprise [license management](../enterprise/manage-enterprise.mdx#license-management)
- notifications: send [Notifications](./events/notifications.md) when events are created
- emails: send emails when triggered by one of the email stages or otherwise

## Schedules

Some tasks run on a schedule. Those schedules can be [configured](#schedule-configuration). Schedules can be manually triggered by clicking the play arrow.

## Tasks statuses

A task can have the following statuses:

- **Successful**: the task executed successfully. No extra action is required.
- **Warning**: the task emitted a warning. Look at the task logs for further information. See [Failed tasks](#failed-tasks) for more details.
- **Error**: the task failed to process. Either the task threw an exception, or reported an other error. Look at the task logs for further information. See [Failed tasks](#failed-tasks) for more details.
- **Waiting to run**: the task has been queued for running, but no worker picked it up yet, either because none are available, they are already busy, or because it's just been queued.
- **Running**: the task is currently running.

## Manage background tasks

### View system tasks

Tasks and schedules can be viewed and managed from the admin interface.

By default, tasks are shown _as close as possible_ to their relevant objects. For instance, LDAP source synchronization tasks and schedules are shown on the LDAP source detail page.

When a task or a schedule cannot be associated to an object (for example housekeeping tasks), it is referred to as "standalone" and will be displayed under **Dashboards** > **System Tasks**. Note that tasks created from a schedule are associated to that schedule and are not considered standalone. Both schedule and task items can be expanded to view additional detail about them.

If you cannot find the object to which a task or schedule is attached to, untick "Show only standalone tasks/schedules" on the **System Tasks** page to show all tasks and schedules, including the ones that are attached to objects.

By default, successful tasks are hidden to minimize the number of shown items. Untick "Exclude successful tasks" to show them.

### Schedule configuration

When schedules are created, they are assigned a default interval. To change that interval, edit the schedule and update it. The format is a crontab.

:::warning
Some tasks are required to run at regular intervals. We only recommend editing synchronization schedules intervals for tuning reasons.
:::

Schedules can also be paused to prevent new tasks to be created from them. They can still be triggered manually while paused. When un-pausing a schedule, it will be triggered immediately.

### Failed tasks

When a task fails, i.e. when the code throws an exception, the task will be retried up to the value configured in [`AUTHENTIK_WORKER__TASK_MAX_RETRIES`](../install-config/configuration/configuration.mdx#authentik_worker__task_max_retries). Tasks that self-reported an error or a warning will not be retried.

Failed tasks will be displayed as any other tasks. Each task can be expanded to show its logs. The logs are split into two parts: "Current execution logs" for the current execution, and "Previous execution logs" for logs from previous execution that happened before a retry was initiated. The information contained in the logs will point to a transient error (a network connection failed for example), a mis-configuration (wrong password set in the LDAP source for example) or a bug in authentik.

#### Restarting tasks

To restart a task, click the retry arrow next to the task. It will be queued again and picked up by a worker.

:::info
To retry tasks created from a schedule, we recommend manually triggering the schedule instead of restarting one of its tasks.
:::
