---
title: X (Twitter)
tags:
    - source
    - x
    - twitter
---

Allows users to authenticate using their X credentials by configuring X as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## X configuration

To integrate X with authentik you will need to create an OAuth application in the X Developer Portal.

1. Log in to the [X Developer Portal](https://developer.twitter.com/).
2. Navigate to **Projects & Apps** > **Overview**.
3. Click the **App Settings** icon (cogwheel) next to the Project App that you want to use. For information on creating a new Project App, refer to the [X Developer Documentation](https://docs.x.com/fundamentals/developer-apps#app-management).
4. Under **User authentication settings**, click **Set up** and set the following required fields:
    - **App permissions**: `Read`
    - **Type of App**: `Web App, Automated App or Bot`
    - **Callback URI / Redirect URL**: `https://authentik.company/source/oauth/callback/x/`
    - **Website URL**: `https://authentik.company`

5. Click **Save**.
6. Take note of the **Client ID** and **Client Secret**. These values will be required in the next section.
7. Click **Done**.

## authentik configuration

To support the integration of X with authentik, you need to create a Twitter OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Twitter OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug which must match the slug used in the X `Callback URI / Redirect URL` field (e.g. `x`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: Enter the Client ID from the X Developer Portal.
            - **Consumer Secret**: Enter the Client Secret from the X Developer Portal.
            - **Scopes** _(optional)_: define any further access scopes.
3. Click **Finish**.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Resources

- [X Developer Portal Documentation](https://docs.x.com/fundamentals/developer-portal)
- [X Developer Documentation - App Management](https://docs.x.com/fundamentals/developer-apps#app-management)
