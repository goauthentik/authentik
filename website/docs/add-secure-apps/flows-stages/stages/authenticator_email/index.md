---
title: Email authenticator setup stage
---

This stage configures an email-based authenticator that sends a one-time codes to a user's email address for authentication.

## Configuration

### Email Settings

The stage can be configured in two ways:
- global settings
or
- stage-specific settings


#### Global settings

Enable the **Use global settings** option to use authentik's global email configuration. This is recommended if you already have email configured in authentik.

#### Stage-specific settings

If you need different email settings for this stage, disable _Use global settings_ and configure the following:

- **Host**: SMTP server hostname (default: localhost)
- **Port**: SMTP server port (default: 25)
- **Username**: SMTP authentication username (optional)
- **Password**: SMTP authentication password (optional)
- **Use TLS**: Enable TLS encryption
- **Use SSL**: Enable SSL encryption
- **Timeout**: Connection timeout in seconds (default: 10)
- **From Address**: Email address messages will be sent from (default: system@authentik.local)

### Message Configuration

- **Token Expiry**: Time in minutes the sent token is valid (default: 30)
- **Subject**: Email subject line (default: "authentik Sign-in code")

## Flow Integration

To use the Email authenticator in a flow:

1. Create a new flow or edit an existing one
2. Add the Email Authenticator Setup Stage
3. Configure the stage settings as described above

When a user goes through this flow, they will:

1. Be prompted for their email address (if not already set)
2. Receive an email with a one-time code
3. Need to enter the code to complete the setup

The email device will be saved and can be used with the [Authenticator validation](../authenticator_validate/index.md) stage for future authentications.
