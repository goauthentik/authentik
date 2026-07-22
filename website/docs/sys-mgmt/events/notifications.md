---
title: Notification Rules
sidebar_label: Notification Rules
---

:::info
To prevent notification loops, events created by policies that are attached to any notification rule do not trigger notifications.
:::

An authentik administrator can create notification rules for selected events. The authentik policy engine filters events through a policy that is bound to a notification rule.

## Workflow overview

To receive notifications about events, follow this workflow:

1. Create a notification transport (or use a default notification transport).
2. Create a policy.
3. Create a notification rule and bind the policy to the rule.

## 1. Create a notification transport

A notification transport determines how authentik delivers notifications to users. Supported delivery methods are local notifications in the authentik UI, email, and webhook. To create a notification transport, see [Create a notification transport](./transports.md#create-a-notification-transport).

## 2. Create a policy

Create a policy that defines which events trigger a notification. For simple conditions, use an Event Matcher policy. For custom logic, use an Expression policy.

### Event Matcher policy

For simple event matching, create and configure an [Event Matcher policy](../../customize/policies/types/event-matcher.md) to define which events trigger a notification. Use the policy's [AKQL query](../akql.mdx#use-akql-in-an-event-matcher-policy) when you need to match event context fields such as `context.geo.country` or `context.authorized_application.name`.

An event must match all configured fields in the policy. Otherwise, the notification rule does not trigger.

### Expression policy for events

To match events with an Expression policy, use code such as the following example:

```python
if "event" not in request.context:
    return False

return ip_address(request.context["event"].client_ip) in ip_network('192.0.2.0/24')
```

For more code examples, see [notification rule expression policies](./notification_rule_expression_policies.mdx).

## 3. Create a notification rule and bind it to the policy

After you create the policies to match the relevant events, create a notification rule.

1. Log in as an administrator, open the authentik Admin interface, and navigate to **Events** > **Notification Rules**.

2. Click **New Notification Rule** to add a new notification rule or click the **Edit** icon next to an existing rule to modify it.

3. Define the rule configuration, and then click **Create Notification Rule** or **Update** to save the settings.

- Use the **Enabled** toggle to turn a rule off without removing its configuration. Disabled rules never create notifications.
- Policies are executed regardless of whether a destination is selected. Notifications are only created when a destination group is selected, or **Send notification to event user** or **Send notification to affected user** is enabled.
- **Send notification to event user** sends the notification to the user that triggered the event. **Send notification to affected user** :ak-version[2026.8] sends it to the user that the event is about, which is not necessarily the same user — when an administrator changes a user's password, the event user is the administrator, and the affected user is the user whose password was changed. This option only has an effect for events that record the affected user in their `subject` context field: [`password_set`](./event-actions.md#password_set), [`user_created`](./event-actions.md#user_created), [`mfa_device_added` and `mfa_device_removed`](./event-actions.md#mfa_device_added--mfa_device_removed), [`login_blocked`](./event-actions.md#login_blocked), and the `user_write` event created by [Account Lockdown](../../security/account-lockdown.md).
- Select which [notification transport](./transports.md) authentik uses to send the notification. Four notification transports are created by default:
    - `default-email-transport`: Delivers notifications via email using the [global email configuration](../../install-config/install/docker-compose.mdx#email-configuration-optional-but-recommended).
    - `default-local-transport`: Delivers notifications within the authentik UI.
    - `default-security-email-transport` and `default-welcome-email-transport` :ak-version[2026.8]: Deliver the emails sent by the default [user security notification rules](./user-security-notifications.md).

4. In the list of notification rules, click the arrow in the row of the notification rule to expand the details of the rule.

5. Click **Create or bind...**. Under **Bind Existing...**, select **Bind an existing policy**. In the **Create Binding** modal, select the policy that you created for this notification rule, and then click **Create**.
