---
title: X (Twitter)
support_level: authentik
---

Allows users to authenticate using their X credentials.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## X configuration

To integrate X with authentik you will need to create an OAuth application in the X Developer Portal.

1. Log in to the [X Developer Portal](https://developer.twitter.com/).
2. Navigate to **Projects & Apps** > **Overview**.
3. Click the **App Settings** icon (cogwheel) next to the Project App that you want to use. Refer to the [X Developer Documentation](https://docs.x.com/fundamentals/developer-apps#app-management) for information on creating a new Project App.
4. Under **User authentication settings**, click **Set up** and set the following required fields:
    - **App permissions**: `Read`
    - **Type of App**: `Web App, Automated App or Bot`
    - **Callback URI / Redirect URL**: `https://authentik.company/source/oauth/callback/twitter/`
    - **Website URL**: `https://authentik.company`

5. Click **Save**.
6. Take note of the **Client ID** and **Client Secret**. These values will be required in the next section.
7. Click **Done**.

## authentik configuration

To support the integration of X with authentik, you need to create a Twitter OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Twitter OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug which must match the slug used in the Twitter `Callback URI / Redirect URL` field (e.g. `twitter`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: `<client_ID>`
            - **Consumer Secret**: `<client_secret>`
            - **Scopes**_(optional)_: define any further access scopes.
3. Click **Finish** to save your settings.

:::info
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/). Note that this is an enterprise feature.
:::

## Resources

- [X Developer Portal Documentation](https://docs.x.com/fundamentals/developer-portal)
- [X Developer Documentation - App Management](https://docs.x.com/fundamentals/developer-apps#app-management)
