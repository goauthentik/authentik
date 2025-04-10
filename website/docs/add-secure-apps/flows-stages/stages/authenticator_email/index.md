---
title: Email Authenticator Setup stage
---

<span class="badge badge--version">authentik 2025.2+</span>

This stage configures an email-based authenticator that sends a one-time code to a user's email address for authentication.

When a user goes through a flow that includes this stage, they are prompted for their email address (if not already set). The user then receives an email with a one-time code, which they enter into the authentik Login panel.

The email address will be saved and can be used with the [Authenticator validation](../authenticator_validate/index.md) stage for future authentications.

## Flow integration

To use the Email Authenticator Setup stage in a flow, follow these steps:

1. [Create](../../flow/index.md#create-a-custom-flow) a new flow or edit an existing one.
2. On the flow's **Stage Bindings** tab, click **Create and bind stage** to create and add the Email Authenticator Setup stage. (If the stage already exists, click **Bind existing stage**.)
3. Configure the stage settings as described below.

    - **Name**: provide a descriptive name, such as Email Authenticator Setup.
    - **Authenticator type name**: define the display name for this stage.
    - **Use global connection settings**: the stage can be configured in two ways: global settings or stage-specific settings.

        - Enable (toggle on) the **Use global connection settings** option to use authentik's global email configuration. Note that you must already have configured your environment variables to use the global settings. See instructions for [Docker Compose](../../../../install-config/install/docker-compose#email-configuration-optional-but-recommended) and for [Kubernetes](../../../../install-config/install/kubernetes#optional-step-configure-global-email-credentials).

        - If you need different email settings for this stage, disable (toggle off) **Use global connection settings** and configure the following options:

        - **Connection settings**:

            - **SMTP Host**: SMTP server hostname (default: localhost)
            - **SMTP Port**: SMTP server port number(default: 25)
            - **SMTP Username**: SMTP authentication username (optional)
            - **SMTP Password**: SMTP authentication password (optional)
                - **Use TLS**: Enable TLS encryption
                - **Use SSL**: Enable SSL encryption
            - **Timeout**: Connection timeout in seconds (default: 10)
            - **From Address**: Email address that messages are sent from (default: system@authentik.local)

        - **Stage-specific settings**:

            - **Subject**: Email subject line (default: "authentik Sign-in code")
            - **Token Expiration**: Time in minutes that the sent token is valid (default: 30)
            - **Configuration flow**: select the flow to which you are binding this stage.

4. Click **Update** to complete the creation and binding of the stage to the flow.

The new Email Authenticator Setup stage now appears on the **Stage Bindings** tab for the flow.
