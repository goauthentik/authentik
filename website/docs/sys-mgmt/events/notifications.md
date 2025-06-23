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

## Create a policy

First you need to create a policy, either the **Event Matcher** policy or a custom Expression policy.

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

## Create a notification rule

After you've created the policies to match the events you want, create a **"**Notification Rule\*\*.

You have to select which group the generated notification should be sent to. If left empty, the rule will be disabled.

:::info
Be aware that policies are executed even when no group is selected.
:::

You also have to select which transports should be used to send the notification.
A transport with the name "default-email-transport" is created by default. This transport will use the [global email configuration](../../install-config/install/docker-compose.mdx#email-configuration-optional-but-recommended).

Starting with authentik 2022.6, a new default transport will be created. This is because notifications are no longer created by default, they are now a transport method instead. This allows for better customization of the notification before it is created.
