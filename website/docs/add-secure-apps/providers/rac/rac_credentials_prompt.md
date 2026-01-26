---
title: RAC Credentials Prompt
---

## About the RAC credentials prompt

You can configure the RAC provider to prompt users for their credentials when connecting to RAC endpoints. This is particularly useful for establishing RDP connections to modern Windows systems that often require credentials to establish a connection.

After implementing this configuration, when connecting to an RAC endpoint users are prompted to enter their credentials which are then passed to the RAC endpoint. This means that static credentials do not need to be set in the RAC provider, property mapping, or endpoint.

This configurations requires:

1. Creating an authorization flow.
2. Creating two prompts.
3. Creating and binding a prompt stage.
4. Updating the RAC provider.

## Create a new authorization flow

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**, click **Create**, and enter the following required settings:
    - **Name**: Enter a descriptive name for the flow.
    - **Title**: Enter a title for the flow. This will be displayed to users when they're prompted for their credentials.
    - **Slug**: Enter a slug for the flow. This will be displayed in the flow URL.
    - **Designation**: `Authorization`
    - **Authentication**: `Require authentication`
3. Click **Create**.

## Create prompts

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Prompts**, click **Create**, and enter the following required settings:
    - **Name**: Enter a descriptive name for the prompt (e.g. `username`).
    - **Field Key**: `connection_settings.username`
    - **Label**: Enter a label for the field which will be displayed above it.
    - **Type**: `Text`
    - **Required**: Toggled on.
    - **Order**: `0`
3. Click **Create** to save the prompt.
4. On the **Prompts** page, click **Create** again, and enter the following required settings:
    - **Name**: Enter a descriptive name for the prompt (e.g. `password`).
    - **Field Key**: `connection_settings.password`
    - **Label**: Enter a label for the field which will be displayed above it.
    - **Type**: `Password`
    - **Required**: Toggled.
    - **Order**: `1`
5. Click **Create** to save the prompt.

:::info
You can optionally add other prompt fields such as `domain` (e.g. `connection_settings.domain`), which can be useful for Windows based RDP. There is also the option of adding a `Text (read-only)` type prompt field that includes explanatory text for the user (e.g. `please enter your RDP credentials`).
:::

## Create and bind a prompt stage

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows**.
3. Click the name of the newly created authorization flow.
4. Click on **Stage bindings**, click **Create and bind stage**, and enter the following required settings:
    - **Select Type**: Select `Prompt stage` as the prompt type.
    - **Create Prompt Stage**:
        - **Name**: Enter a name for the prompt stage.
        - Under **Fields**:
            - Click the **x** icon to remove all selected fields.
            - Add the two newly created prompt fields (e.g.`username` and `password`) to selected fields.
        - Under **Validation Policies**:
            - Click the **x** icon to remove all selected validation policies.
    - **Create binding**:
        - Click **Finish**.

## Update the RAC provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers**.
3. Click the **Edit** icon of the RAC provider that you wish to add a credentials prompt to.
4. Change **Authorization flow** to the newly created authorization flow.
5. Click **Update** to save the change.

## Update the RAC endpoint _(sometimes required)_

Depending on the configuration of the RDP server that's being connected to, it is sometimes necessary to set the security type that's used for the connection. For many modern windows RDP servers, this often needs to be set to `tls`.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the name of the RAC provider that you're using.
3. Under **Endpoints**, click the **Edit** icon of the endpoint that you're using.
4. Under **Advanced Settings** in the **Settings** box, enter `security: tls`
5. Click **Update** to save the change.

:::info
Other options for the connection security type are: `any`, `nla`, `nla-ext`, `vmconnect`, and `rdp`. For more information see the [Guacamole RDP Authentication and Security Documentation](https://guacamole.apache.org/doc/gug/configuring-guacamole.html#authentication-and-security).
:::

## Configuration verification

Log in to authentik with a user account that has the required privileges to access the RAC application. Open the User interface, and on the **My applications** page click the RAC application. You should then be redirected to the prompt stage and prompted for a username and password. Enter the credentials for the RAC endpoint and if the credentials are valid the RDP/SSH/VNC connection should be established.
