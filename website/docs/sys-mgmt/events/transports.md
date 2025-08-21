---
title: Transport rules
sidebar_label: Transport rules
---

To receive notifications about events you must first [create a notification transport](#create-a-notification-transport), and then define a notification rule with a bound policy. For more information, see the [Workflow overview](./notifications.md#workflow-overview).

## Notification transport modes

Notifications can be sent to users via multiple mediums, or _transports_:

- Local (in the authentik user interface)
- Email
- Webhook (generic)
- Webhook (Slack/Discord)

### Local

This notification transport will manifest the notification within the authentik user interface (UI).

### Email

Select this transport to send event notifications to an email address. Note that by default the [global email configuration](../../install-config/install/docker-compose.mdx#email-configuration-optional-but-recommended) is used.

To edit an email address, follow the same instructions as above for configuring the global email during the installation process.

### Webhook (generic)

This will send a POST request to the given URL with the following contents:

```json
{
    "body": "body of the notification message",
    "severity": "severity level as configured in the trigger",
    // User that the notification was created for, i.e. a member of the group selected in the rule
    "user_email": "notification user's email",
    "user_username": "notification user's username",
    // User that created the event
    "event_user_email": "event user's email",
    "event_user_username": "event user's username"
}
```

The `Content-Type` header is set to `text/json`.

#### Webhook mappings

You can use Webook mappings to configure the request's payload and/or header. These are a type of property mapping that can be applied to the `Webhook Body Mapping` or `Webhook Header Mapping` fields of the webhook notification transport.

##### Webhook body example

An example of a webhook body mapping that sets a `foo` key with its value set to the body of the notification:

```python
return {
    "foo": request.context['notification'].body,
}
```

##### Webhook header example

An example of a webhook header mapping that sets an authorization key:

```python
return {
  "Authorization": "Bearer <token>"
}
```

### Webhook (Slack or Discord)

This sends a request using the Slack-specific format. This is also compatible with Discord's webhooks by appending `/slack` to the Discord webhook URL.

## Create a notification transport

1. Log in as an administrator to the authentik Admin interface, and then navigate to **Event > Notification Transports**.

2. Click **Create** to add a new transport or click the **Edit** icon next to an existing notification transport to modify it.

3. Define the **Name** and **Mode** for the notification transport, enter required configuration settings, and then click **Create**.
