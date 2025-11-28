---
title: Notification rules
sidebar_label: Notification rules
---

:::info
To prevent infinite loops of cause and effect (events created by policies which are attached to a notification rule), _any events created by a policy which is attached to any notification rules do not trigger notifications._
:::

An authentik administrator can create notification rules based on the creation of specified events. Filtering of events is processed by the authentik Policy Engine, using a combination of both 1) a policy and 2) a notification rule.

## Workflow overview

To receive notifications about events, follow this workflow:

1. Create a notification transport (or use a default notification transport).
2. Create a policy.
3. Create a notification rule and bind the policy to the rule.

## 1. Create a notification transport

A notification transport determines the method used to deliver notifications to users. Supported delivery methods are: local notifications displayed in the authentik UI, email, and webhook. Follow these [instructions](./transports.md#create-a-notification-transport) to create a notification transport.

## 2. Create a policy

You will need to create a policy (either the **Event Matcher** policy or a custom Expression policy) that defines which events will trigger a notification.

### Event Matcher policy

For simple event matching you can [create and configure](../../customize/policies/working_with_policies.md) an **Event Matcher policy** to define which events (known as _Actions_ in the policy) will trigger a notification. For example, whenever a user deletes a model object, or whenever any user fails to successfully log in.

Be aware that an event has to match all configured fields in the policy, otherwise the notification rule will not trigger.

### Expression policy for events

To match events with an **Expression Policy**, you can write code like so:

```python
if "event" not in request.context:
    return False

return ip_address(request.context["event"].client_ip) in ip_network('192.0.2.0/24')
```

For more code examples, see [notification rule expression policies](./notification_rule_expression_policies.mdx).

## 3. Create a notification rule and bind it to the policy

After you've created the policies to match the events you want, create a notification rule.

1. Log in as an administrator, open the authentik Admin interface, and navigate to **Event > Notification Rules**.

2. Click **Create** to add a new notification rule or click the **Edit** icon next to an existing rule to modify it.

3. Define the policy configurations, and then click **Create** or **Update** to save the settings.

- Note that policies are executed regardless of whether a group is selected. However, notifications are only triggered when a group is selected.
- You also have to select which [notification transport](./transports.md) should be used to send the notification. Two notification transports are created by default:
    - `default-email-transport`: Delivers notifications via email using the [global email configuration](../../install-config/install/docker-compose.mdx#email-configuration-optional-but-recommended).
    - `default-local-transport`: Delivers notifications within the authentik UI.

4. In the list of notification rules, click the arrow in the row of the notification rule to expand the details of the rule.

5. Click **Bind existing Policy/Group/User** and in the **Create Binding** modal, select the policy that you created for this notification rule and then click **Create** to finalize the binding.

:::info
Be aware that policies are executed even when no group is selected.
:::
