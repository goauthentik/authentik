---
title: Transports
---

To receive notifications about events, you will need to [create](#create-a-transport) a transport object, then create a notification rule and a policy. For details on this workflow refer to

## Transport modes

Notifications can be sent to users via multiple mediums, or _transports_:

- Local
- Email
- Webhook (generic)
- Webhook (Slack/Discord)

### Local transport

This transport will manifest the notification within the authentik user interface (UI).

### Email

select this transport to send event notificstions to an email address. Note that by default, the [global email configuration](../../install-config/install/docker-compose.mdx#email-configuration-optional-but-recommended) is used.

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

Starting in 2021.9, you can also select a Notification mapping. This allows you to freely configure the request's payload. For example:

```python
return {
    "foo": request.context['notification'].body,
}
```

### Webhook (Slack or Discord)

This sends a request using the Slack-specific format. This is also compatible with Discord's webhooks by appending `/slack` to the Discord webhook URL.

## Create a transport

1. Log in as an administrator, open the authentik Admin interface, and navigate to **Event > Notification Transports**.

2. Click **Create** to add a new transport, or click the **Edit** icon next to an existing transport to modify it.

3. Define the **Name** and **Mode** for the transport, enter required configuration settings, and then click **Create**.

