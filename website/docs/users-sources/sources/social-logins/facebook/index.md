---
title: Facebook
tags:
    - source
    - facebook
    - meta
---

Allows users to authenticate using their Facebook credentials by configuring Facebook as a federated identity provider via OAuth2.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## Facebook configuration

To integrate Facebook with authentik you will need to create an OAuth application in the Meta for Developers Dashboard.

1. Log in to the [Meta for Developers Dashboard](https://developers.facebook.com/) with your Facebook account.
2. After logging in, [register as a developer](https://developers.facebook.com/async/registration). Refer to the [Facebook development documentation](https://developers.facebook.com/docs/development) for more information.

After registering, you need to create an application so that Facebook generates a unique ID for authentik.

3. On the [Meta for Developers Dashboard](https://developers.facebook.com/) click **Create**.
4. Follow the prompts to create the application.

After creating the application you need to customize its login settings.

5. On the [Meta for Developers Dashboard](https://developers.facebook.com/) click **Use Cases** in the left navigation pane.
6. Under **Authentication and account creation** click **Customize** and then **Go to settings**.
7. Set the **Valid OAuth redirect URIs** field to `https://authentik.company/source/oauth/callback/facebook/` and then click **Save**.
8. Navigate to the **Use cases** > **Customize** page.
9. Under **Permissions** click **Add** for the **email** permission.

Next, you need to obtain the **App ID** and **App Secret** for the Facebook app. These will be required when creating the source in authentik.

10. Go back to the Dashboard, and in the bottom left of the navigation pane, click **App settings** > **Basic**.
11. Take note of the **App ID** and the **App secret** values.

Finally, you need to publish the Facebook app.

12. Go back to the Dashboard, and on the **Create and publish this app** page, follow the prompts to complete the process.

## authentik configuration

To support the integration of Facebook with authentik, you need to create a Facebook OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **Create**, and then configure the following settings:
    - **Select type**: select **Facebook OAuth Source** as the source type.
    - **Create Facebook OAuth Source**: provide a name, a slug which must match the slug used in the Facebook `Valid OAuth redirect URIs` field (e.g. `facebook`), and the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: enter the **App ID** from Facebook.
            - **Consumer Secret**: enter the **App Secret** from Facebook.
            - **Scopes** _(optional)_: define any further access scopes.
3. Click **Finish** to save your settings.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

## Resources

- [Meta for Developers Documentation - Facebook Login Overview](https://developers.facebook.com/docs/facebook-login/overview)
