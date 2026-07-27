---
title: Log in with Instagram
sidebar_label: Instagram
tags:
    - source
    - instagram
    - meta
---

This source lets users authenticate with their Instagram credentials by configuring Instagram as a federated identity provider with OAuth 2.0.

:::warning Professional accounts only
Instagram Login uses the Instagram API with Instagram Login, which only supports Instagram **professional** accounts (Business or Creator). Personal Instagram accounts cannot authenticate through this source: Meta permanently shut down the Instagram Basic Display API, which was the only integration that supported consumer accounts, on December 4, 2024.
:::

:::info No email address
Instagram does not expose an email address for the authenticated user. As a result, the source cannot populate the user's email during enrollment. If your enrollment flow requires an email, add a [Prompt stage](../../../../add-secure-apps/flows-stages/stages/prompt/index.md) to collect one, or map it with a [source property mapping](../../property-mappings/index.md).
:::

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

You need an Instagram professional (Business or Creator) account. If your account is personal, convert it to a professional account in the Instagram app before continuing.

## Instagram configuration

To integrate Instagram with authentik, create an app in the Meta for Developers Dashboard and add the Instagram API use case to it.

1. Log in to the [Meta for Developers Dashboard](https://developers.facebook.com/) and, if you have not already, [register as a developer](https://developers.facebook.com/async/registration).
2. On the [Meta for Developers Dashboard](https://developers.facebook.com/) click **Create app**.
3. Under **Use cases**, select **Manage messaging & content on Instagram**.
4. Open your app's **Use cases** page, find **Manage messaging & content on Instagram**, and click **Customize**.
5. On the **Customize use case** page, in the left panel select **API setup with Instagram login**.
6. Scroll down to **4. Set up Instagram business login** and click **Set up**. Add `https://authentik.company/source/oauth/callback/instagram/` as an OAuth redirect URI, then save.
7. At the top of that panel, take note of the **Instagram app ID** and the **Instagram app secret**. These will be required when creating the source in authentik.

## authentik configuration

To support the integration of Instagram with authentik, you need to create an Instagram OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **New Source**, and then configure the following settings:
    - **Select type**: select **Instagram OAuth Source** as the source type.
    - **Create Instagram OAuth Source**: provide a name, a slug that must match the slug used in the OAuth redirect URI (e.g. `instagram`), and the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: enter the **Instagram app ID** from Instagram.
            - **Consumer Secret**: enter the **Instagram app secret** from Instagram.
            - **Scopes** _(optional)_: define any further access scopes. Note that Instagram expects `instagram_business_*` scopes, comma-separated.
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

- [Meta for Developers Documentation - Instagram API with Instagram Login](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login)
- [Meta for Developers Documentation - Business Login for Instagram](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-login)
