---
title: Configuration
sidebar_label: Configuration
tags: [authentik Agent, connector, configure, configuration]
---

Before deploying the authentik Agent, configure your authentik deployment. This involves:

- Create and apply a OAuth [Device code flow](../../add-secure-apps/providers/oauth2/device_code.md)
- Creating an OAuth application and provider
- Creating a [Connector](../device-compliance/connectors.md)

## Create and apply a OAuth device code flow

The OAuth device code flow enables secure authentication for input-limited clients like CLI tools and is required for the authentik Agent to function.

If you have already deployed the authentik OAuth device code flow, skip to the [next section](#create-an-application-and-provider-in-authentik-for-cli).

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Flows and Stages** > **Flows** and click **Create**.
3. Set the following required configurations:
    - **Name**: provide a name (e.g. `default-device-code-flow`)
    - **Title**: provide a title (e.g. `Device code flow`)
    - **Slug**: provide a slug (e.g `default-device-code-flow`)
    - **Designation**: `Stage Configuration`
    - **Authentication**: `Require authentication`
4. Click **Create**.
5. Navigate to **System** > **Brands** and click the **Edit** icon on the default brand.
6. Set **Default code flow** to the newly created device code flow and click **Update**.

## Create an application and provider in authentik for CLI

The authentik agent requires an OAuth application/provider pair to handle authentication.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name (e.g. `authentik-cli`), an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **Client type** to `Public`.
        - Set the **Client ID** to `authentik-cli`.
        - Select any available signing key.
        - Under **Advanced protocol settings**:
            - In addition to the three default **Selected Scopes**, add the `authentik default OAuth Mapping: OpenID 'offline_access'` scope.
    - **Configure Bindings** _(optional)_: you can create a [binding](../../../add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage access to the application.

3. Click **Submit** to save the new application and provider.

## Create the authentik Agent connector

The authentik Agent [Connector](../device-compliance/connectors.md) allows device information to be reported to authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors** and click **Create**.
3. Select **Agent Connector** as the agent type and click **Next**.
4. Configure the following required settings:
    - **Connector name**: provide a descriptive name (e.g. `authentik Agent`)
    - **Refresh interval**: select how often the agent will attempt to update its configuration.
    - **Enabled**: toggle to enable the connector.
    - Under **Authentication settings**:
        - **Federated OIDC Providers**: add the `authentik-cli` provider that you created in the previous section.
5. Click **Finish**.
