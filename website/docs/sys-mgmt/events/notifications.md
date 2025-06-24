---
title: Notifications
---

:::note
To prevent infinite loops of cause and effect (events created by policies which are attached to a notification rule), _any events created by a policy which is attached to any notification rules do not trigger notifications._
:::

An authentik administrator can create notification rules based on the creation of specified events. Filtering of events is processed by the authentik Policy Engine, using a combination of both 1) a policy and 2) a notification rule.

## Workflow overview

To receive notifications about events, follow this workflow:

1. [Create a transport](./transports.md#create-a-transport) (or use an existing default transport)
2. [Create a policy](#create-a-policy)
3. [Create a notification rule, and bind the policy to the rule](#create-a-notification-rule)

## 1. Create a notification transport



## 2. Create a policy

First you need to create a policy (either the **Event Matcher** policy or a custom Expression policy) that defines which events will trigger a notification.

### **Event Matcher** policy

For simple filtering you can [create and configure](../../customize/policies/working_with_policies.md) a new **Event Matcher** policy to specify exactly which events (known as _Actions_ in the policy) you want to be notified about. For example, you get chose to create a policy for every time a user deletes a model object, or fails to successfully log in.

The authentik policy engine....

Be aware that an event has to match all configured fields in the policy, otherwise the notification rule will not trigger.

### Expression policy for events

To match events with an "Expression Policy", you can write code like so:

```python
if "event" not in request.context:
    return False

return ip_address(request.context["event"].client_ip) in ip_network('192.0.2.0/24')
```

## 3. Create a notification rule and bind it to the policy

After you've created the policies to match the events you want, create a notification rule.

1. Log in as an administrator, open the authentik Admin interface, and navigate to **Event > Notification Rules**.

2. Click **Create** to add a new notification rule, or click the **Edit** icon next to an existing rule to modify it.

3. Define the ------------, and then

You have to select which group the generated notification should be sent to. If left empty, the rule will be disabled.

:::info
Be aware that policies are executed even when no group is selected.
:::

You also have to select which [transports](./transports.md) should be used to send the notification.
A transport with the name "default-email-transport" is created by default. This transport will use the [global email configuration](../../install-config/install/docker-compose.mdx#email-configuration-optional-but-recommended).

4. Click **Create**.




