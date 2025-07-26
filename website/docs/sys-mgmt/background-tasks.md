---
title: Background tasks
slug: /background-tasks
---

authentik uses background tasks to run various operations independently and asynchronously, separated from the continuous web requests processed for general user interaction. These background tasks are run by the [worker](./ops/worker.md).

## What are background tasks used for?

Here is a non-exhaustive list of what background tasks are used for:

- Outposts: manage [outpost](../add-secure-apps/outposts/index.mdx) deployments, send notifications to outpost when a refresh is needed
- Housekeeping: clean up old objects, check for updates, etc.
- Blueprints: import and apply [Blueprints](../customize/blueprints/index.mdx)
- Synchronization: sync users to and from authentik, from sources and to providers. This is used by:
    - [SCIM Provider](../add-secure-apps/providers/scim/index.md)
    - [Google Workspace Provider](../add-secure-apps/providers/gws/index.md)
    - [Microsoft Entra Provider](../add-secure-apps/providers/entra/index.md)
    - [SSF Provider](../add-secure-apps/providers/ssf/index.md)
    - [Kerberos Source](../users-sources/sources/protocols/kerberos/index.md)
    - [LDAP Source](../users-sources/sources/protocols/ldap/index.md)
- Enterprise [license management](../enterprise/manage-enterprise.mdx#license-management)
- Event Notifications: send [Notifications](./events/notifications.md) when events are created
- Emails: send emails when triggered by one of the email stages or otherwise

## Schedules

authentik runs some tasks on a schedule. Schedules can be [configured](#schedule-configuration) or manually triggered by clicking the play arrow.

## Tasks statuses

A task can have the following statuses:

- **Successful**: the task executed successfully. No extra action is required.
- **Warning**: the task emitted a warning. Look at the task logs for further information. See [Failed tasks](#failed-tasks) for more details.
- **Error**: the task failed to process. Either the task threw an exception, or reported an other error. Look at the task logs for further information. See [Failed tasks](#failed-tasks) for more details.
- **Waiting to run**: the task has been queued for running, but no worker has picked it up yet, either because none are available, they are already busy, or because it's just been queued.
- **Running**: the task is currently running.

## Manage background tasks

### View system tasks

You can view and manage all background tasks and schedules from the Admin interface.

However, by default, tasks are shown _as close as possible_ to their relevant objects. For instance, LDAP source synchronization tasks and schedules are shown on the LDAP source detail page.

When a task or a schedule cannot be associated to an object (for example, housekeeping tasks), it is referred to as "standalone" and is displayed under **Dashboards** > **System Tasks**. Note that tasks created from a schedule are associated to that schedule and thus are not considered standalone. Both schedule and task items can be expanded to view additional details about them.

If you cannot find the object to which a task or schedule is attached, deselect the "Show only standalone tasks/schedules" toggle on the **System Tasks** page to show all tasks and schedules, including the ones that are attached to objects.

By default, successful tasks are hidden to minimize the number of shown items. Deselect "Exclude successful tasks" to display them.

### Schedule configuration

When the authentik system creates a schedule it is assigned a default interval. The schedule uses a format based on [unix-cron](https://man7.org/linux/man-pages/man5/crontab.5.html).

To change that interval, click the Edit icon for the specific schedule and update it.

:::warning
Some tasks are required to run at regular intervals. For tuning reasons we recommend editing the intervals only for synchronization schedules, not for other types of schedules.
:::

Schedules can also be _paused_ to prevent new tasks to be created from them. They can still be triggered manually while paused. When you un-pause a schedule, it will be triggered immediately.

### Failed tasks

When a task fails, i.e. when the code throws an exception, the task will be retried as many times as the value configured in [`AUTHENTIK_WORKER__TASK_MAX_RETRIES`](../install-config/configuration/configuration.mdx#authentik_worker__task_max_retries). Tasks that self-reported an error or a warning will not be retried.

Failed tasks will be displayed like any other tasks. Each task can be expanded to show its logs. The logs are split into two parts: "Current execution logs" for the current execution, and "Previous execution logs" for logs from previous executions that happened before a retry was initiated. The information contained in the logs indicate either a transient error (a network connection failed for example), a mis-configuration (wrong password set in the LDAP source for example), or a bug in authentik.

#### Restarting tasks

To restart a task, click the retry arrow next to the task. It will be queued again and picked up by a worker.

:::info
To retry tasks created from a schedule, we recommend manually triggering the schedule (click the Run arrow beside the schedule) instead of restarting one of its tasks.
:::
