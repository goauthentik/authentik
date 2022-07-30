---
title: Transports
---

Notifications can be sent to users via multiple mediums. By default, the [global email configuration](../installation/docker-compose#email-configuration-optional-but-recommended) will be used.

## Generic Webhook

This will send a POST request to the given URL with the following contents:

```json
{
    "body": "body of the notification message",
    "severity": "severity level as configured in the trigger",
    "user_email": "user's email",
    "user_username": "user's username"
}
```

The `Content-Type` header is set to `text/json`.

Starting in 2021.9, you can also select a Notification mapping. This allows you to freely configure the request's payload. For example:

```python
return {
    "foo": context['notification'].body,
}
```

## Slack Webhook

This sends a request using the Slack-specific format. This is also compatible with Discord's webhooks by appending `/slack` to the Discord webhook URL.
