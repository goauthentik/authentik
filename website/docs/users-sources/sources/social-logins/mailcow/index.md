---
title: Mailcow
tags:
    - source
    - mailcow
---

Allows users to authenticate using their Mailcow credentials by configuring Mailcow as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `mailcow.company` is the FQDN of the Mailcow installation.

## Mailcow configuration

To integrate Mailcow with authentik you will need to create an OAuth application in Mailcow.

1. Log in to Mailcow as an administrator
2. Navigate to **System** > **Configuration**, and then **Access** > **OAuth2 Apps**.
3. Click **Add OAuth2 client** and provide the **Redirect URI**: `https://authentik.company/source/oauth/callback/mailcow/`
4. Take note of the **Client ID** and **Client Secret**. These values will be required in the next section.

## authentik configuration

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug which must match the slug used in the Mailcow `Redirect URI` field (e.g. `mailcow`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: `<client_ID>`
            - **Consumer Secret**: `<client_secret>`
            - **Scopes** _(optional)_: define any further access scopes.
        - **URL Settings**
            - **Authorization URL**: `https://mailcow.company/oauth/authorize`
            - **Access token URL**: `https://mailcow.company/oauth/token`
            - **Profile URL**: `https://mailcow.company/oauth/profile`
3. Click **Finish** to save your settings.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.
