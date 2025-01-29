---
title: Email Authenticator Setup stage
---

This stage configures an email-based authenticator that sends a one-time code to a user's email address for authentication.

## Configuration

### Email settings

The stage can be configured in two ways:
- global settings
or
- stage-specific settings


#### Global settings

Select the **Use global settings** option to use authentik's global email configuration. Note that you must already have configured your environment variables to use the global settings. See instructions for [Docker Compose](../../install-config/install/docker-compose#email-configuration-optional-but-recommended) and for [Kubernetes](../../../install-config/install/kubernetes#optional-step-configure-global-email-credentials).

#### Stage-specific settings

If you need different email settings for this stage, unselect **Use global settings** and configure the following settings:

- **Host**: SMTP server hostname (default: localhost)
- **Port**: SMTP server port (default: 25)
- **Username**: SMTP authentication username (optional)
- **Password**: SMTP authentication password (optional)
- **Use TLS**: Enable TLS encryption
- **Use SSL**: Enable SSL encryption
- **Timeout**: Connection timeout in seconds (default: 10)
- **From Address**: Email address messages will be sent from (default: system@authentik.local)

### Message Configuration

- **Token Expiry**: Time in minutes that the sent token is valid (default: 30)
- **Subject**: Email subject line (default: "authentik Sign-in code")

## Flow integration

To use the Email Authenticator Setup stage in a flow:

1. [Create](../..//stages/#create-a-stage) a new Email Authenticator Setup stage (or verify that there is already one).
2. [Create](../../flow/#create-a-custom-flow) a new flow or edit an existing one.
2. On the flow's **Stage Bindings** tab, add the Email Authenticator Setup stage.
3. Configure the stage settings as described above

When a user goes through this flow, they will:

1. Be prompted for their email address (if not already set)
2. Receive an email with a one-time code
3. Need to enter the code to complete the setup

The email device will be saved and can be used with the [Authenticator validation](../authenticator_validate/index.md) stage for future authentications.
