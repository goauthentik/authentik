---
title: Event Matcher Policy
tags:
    - policy
    - events
    - notifications
---

Use an Event Matcher policy when you want to match authentik events against a small set of built-in fields instead of writing a custom expression.

This policy is most commonly used with [Notification Rules](../../../sys-mgmt/events/notifications.md).

## When to use it

Use an Event Matcher policy when you want to match against events such as:

- a failed login
- a model being created, updated, or deleted
- activity from a specific authentik app
- activity from a specific client IP

For more complex matching, such as network ranges or logic across multiple event fields, use an [Expression policy](./expression/index.mdx) instead.

## What it matches

An Event Matcher policy can match on:

- action
- app
- model
- exact client IP

Any field you leave empty is treated as a wildcard. Any field you configure must match for the policy to pass.

:::info Event Context
This policy is useful only when an event object is present in the policy context, such as when a notification rule evaluates an event.
:::

## Create an Event Matcher policy

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Click **New Policy** and select **Event Matcher Policy**.
4. Configure the fields you want to match.
5. Click **Create Policy**.

## Send notifications about an event match

To send notifications for a subset of authentik events:

1. Create an Event Matcher policy.
2. Create or edit a [Notification Rule](../../../sys-mgmt/events/notifications.md).
3. Bind the policy to that notification rule.

Be aware that an event has to match all configured fields in the policy, otherwise the notification rule will not trigger.
