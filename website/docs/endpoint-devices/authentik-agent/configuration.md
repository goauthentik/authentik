---
title: Configuration
sidebar_label: Configuration
tags: [authentik Agent, connector, configure, configuration]
---

To support the deployment of the authentik Agent on endpoint devices, you need to configure your authentik deployment. This involves importing the [device code flow](../../add-secure-apps/providers/oauth2/device_code.md), creating an application/provider pair, and creating a [Connector](../device-compliance/connectors.md).

## Import OAuth device code flow

(TODO) Intro sentence

If you have already deployed the authentik OAuth device code flow, skip to the next section.

1. Download the [device code flow blueprint file](https://raw.githubusercontent.com/goauthentik/platform/refs/heads/main/hack/authentik/blueprints/oauth2-device-code.yaml).
2. Log in to authentik as an administrator and open the authentik Admin interface.
3. Navigate to **Flows and Stages** > **Flows**.
4. Click **Import**
5. Select the downloaded blueprint and click **Import**.
6. Navigate to System > Brands and click the Edit icon on the default brand.
7. Set Default code flow to the newly created device code flow and click Update.

Alternatively, manually create the flow by following the instructions in the [Device code flow documentation](../../add-secure-apps/providers/oauth2/device_code.md#create-and-apply-a-device-code-flow).

## Create an application and provider in authentik for CLI

(TODO) Intro sentence

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
    - **Configure Bindings** _(optional)_: you can create a [binding](../add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage access to the application.

3. Click **Submit** to save the new application and provider.

## Create the authentik Agent connector

(TODO) Intro sentence

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Endpoint Devices** > **Connectors**, click **Create**, and configure the following settings:
    - **Name** - provide a descriptive name (e.g. `authentik Agent`)
    - **blah** -

## Configuration verification
