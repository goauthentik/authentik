---
title: Notification Transports
sidebar_label: Notification Transports
---

To receive notifications about events, first [create a notification transport](#create-a-notification-transport), and then define a notification rule with a bound policy. For more information, see the [workflow overview](./notifications.md#workflow-overview).

## Notification transport modes

Notifications can be sent to users through multiple delivery methods, or _transports_:

- Local (in the authentik user interface)
- Email
- Webhook (generic)
- Webhook (Slack/Discord)

### Local

This notification transport creates a notification in the authentik UI.

### Email

Select this transport to send event notifications to an email address. By default, authentik uses the [global email configuration](../../install-config/install/docker-compose.mdx#email-configuration-optional-but-recommended).

To edit the email address used by the transport, update the global email configuration from your installation method.

#### Custom email template

The email template that's used by a transport can be selected via the **Email Template** setting. Configured [Custom email templates](../../add-secure-apps/flows-stages/stages/email/index.md#custom-templates) can also be seleced.

The context that's available when sending an email via a notification transport include:

<!-- prettier-ignore -->
```html
{{ key_value.user_email }} # email address of the user being emailed
{{ key_value.user_username}} # username of the user being emailed
{{ key_value.http_request.* }} # values from the http_request linked to the generation of the email
{{ body }} # body of the event that triggered the notification
{{ title }} # title of the event that triggered the notification
{{ link.target }} # URL included in the event, only available in data export and custom events
{{ link.label }} # URL label included in the event, only available in data export and custom events
```

### Webhook (generic)

This transport sends a POST request to the configured URL. The default body includes the notification body, severity, notification recipient, and triggering event user.

```json
{
    "body": "body of the notification message",
    "severity": "severity level as configured in the trigger",
    "user_email": "notification user's email",
    "user_username": "notification user's username",
    "event_user_email": "event user's email",
    "event_user_username": "event user's username"
}
```

The `Content-Type` header is set to `application/json`.

##### Webhook Certificate Authority

If the server in the webhook URL does not have a certificate issued by a public certificate authority, select a Certificate-Keypair to validate the server certificate. If no keypair is selected, authentik uses the root certificates from [mkcert.org](https://mkcert.org/).

#### Webhook mappings

You can use webhook mappings to configure the request payload, headers, or both. Webhook mappings are property mappings that can be applied to the **Webhook Body Mapping** or **Webhook Header Mapping** fields of the webhook notification transport.

##### Webhook body examples

The following webhook body mapping sets a `foo` key to the body of the notification:

```python
return {
    "foo": request.context['notification'].body,
}
```

You can also include fields from the notification recipient and the triggering event:

```python
return {
    "email": request.user.email,
    "client_ip": notification.event.client_ip,
}
```

For failed login notifications, the attempted username is stored in the event context. If the GeoIP and ASN context processors are configured, their data is also available in the event context:

```python
event = notification.event

return {
    "action": event.action,
    "username": event.context.get("username"),
    "client_ip": event.client_ip,
    "geo": event.context.get("geo"),
    "asn": event.context.get("asn"),
}
```

##### Webhook header example

The following webhook header mapping sets an authorization key:

```python
return {
  "Authorization": "Bearer <token>"
}
```

### Webhook (Slack or Discord)

This transport sends a request using the Slack-specific format. It is also compatible with Discord webhooks when you append `/slack` to the Discord webhook URL.

## Create a notification transport

1. Log in as an administrator, open the authentik Admin interface, and navigate to **Event > Notification Transports**.

2. Click **New Notification Transport** to add a new transport or click the **Edit** icon next to an existing notification transport to modify it.

3. Define the **Name** and **Mode** for the notification transport, enter required configuration settings, and then click **Create Notification Transport**.
