---
title: Twitch
tags:
    - source
    - twitch
---

Allows users to authenticate using their Twitch credentials by configuring Twitch as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## Twitch configuration

To integrate Twitch with authentik you will need to create an OAuth application in the Twitch Developers Console.

1. Log in to the [Twitch Developers Console](https://dev.twitch.tv/console).
2. Next to **Applications** click **Register Your Application** and set the following fields:
    - **Name**: `authentik`
    - **OAuth Redirect URLs**: `https://authentik.company/source/oauth/callback/twitch`
    - **Category**: select a category for your application

3. Click **Create** to finish the registration of your application.
4. Next to your newly created application, click **Manage**.
5. Generate a secret by clicking **New Secret**.
6. Take note of the **Client ID** and **Client Secret**. This value will be required in the next section.
7. Click **Save**.

## authentik configuration

To support the integration of Twitch with authentik, you need to create an Twitch OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Twitch OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug which must match the slug used in the Twitch `OAuth Redirect URLs` field (e.g. `twitch`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: `<client_ID>`
            - **Consumer Secret**: `<client_secret>`
            - **Scopes** _(optional)_: define any further access scopes.
3. Click **Finish** to save your settings.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

## Resources

- [Twitch Developer Documentation](https://dev.twitch.tv/docs)
