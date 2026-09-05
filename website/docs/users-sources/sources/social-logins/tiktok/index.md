---
title: Log in with TikTok
sidebar_label: TikTok
tags:
    - source
    - tiktok
---

This source lets users authenticate with their TikTok credentials by configuring TikTok as a federated identity provider with OAuth 2.0.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

## TikTok configuration

To integrate TikTok with authentik, register an app with Login Kit on the [TikTok for Developers](https://developers.tiktok.com/) portal.

1. Register for a developer account on [TikTok for Developers](https://developers.tiktok.com/) and create an app.
2. Add the **Login Kit** product to the app.
3. Under Login Kit, add a **Redirect URI** of `https://authentik.company/source/oauth/callback/tiktok/`.
4. Request the `user.info.basic` scope for the app.
5. Submit the app for review. TikTok only issues authorizations to end users once the app is approved.
6. From the app's **Credentials** page, note the **Client key** and **Client secret**.

:::warning HTTPS required
TikTok requires the redirect URI to use HTTPS. A plain `http://` callback, including `localhost`, is rejected at the authorization step.
:::

## authentik configuration

To support the integration of TikTok with authentik, you need to create a TikTok OAuth source in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Federation and Social login**, click **New Source**, and then configure the following settings:
    - **Select type**: select **TikTok OAuth Source** as the source type.
    - **Create OAuth Source**: provide a name, a slug (e.g. `tiktok`), and set the following required configurations:
        - **Protocol settings**
            - **Consumer Key**: Enter the **Client key** from the TikTok app.
            - **Consumer Secret**: Enter the **Client secret** from the TikTok app.
            - **Scopes**: define any further access scopes.
3. Click **Finish**.

:::info Display new source on login screen
For instructions on how to display the new source on the authentik login page, refer to the [Add sources to default login page documentation](../../index.md#add-sources-to-default-login-page).
:::

:::info Embed new source in flow :ak-enterprise
For instructions on embedding the new source within a flow, such as an authorization flow, refer to the [Source Stage documentation](../../../../../add-secure-apps/flows-stages/stages/source/).
:::

## Source property mappings

Source property mappings allow you to modify or gather extra information from sources. See the [overview](../../property-mappings/index.md) for more information.

The following data is retrieved from TikTok and mapped to the user's attributes in authentik:

| TikTok Field              | authentik Attribute     | Description                     |
| :------------------------ | :---------------------- | :------------------------------ |
| `union_id` (or `open_id`) | `username`              | Used as the primary identifier. |
| `display_name`            | `name`                  | The user's display name.        |
| `avatar_url`              | `attributes.avatar_url` | URL to the user's avatar.       |
| `open_id`                 | `attributes.open_id`    | Per-app user identifier.        |
| `union_id`                | `attributes.union_id`   | Cross-app user identifier.      |

### User matching

TikTok users are identified by their `union_id` (if available) or `open_id`.

- **Union ID**: Unique across all apps owned by the same developer account. authentik prioritizes this as the username.
- **Open ID**: Unique to the specific app. Used as a fallback if `union_id` is not returned.

:::info No email address
TikTok does not expose an email address for the authenticated user. As a result, the source cannot populate the user's email during enrollment. If your enrollment flow requires an email, add a [Prompt stage](../../../../add-secure-apps/flows-stages/stages/prompt/index.md) to collect one, or map it with a [source property mapping](../../property-mappings/index.md).
:::

## Resources

- [TikTok for Developers](https://developers.tiktok.com/)
- [Login Kit for Web](https://developers.tiktok.com/doc/login-kit-web/)
- [Manage user access tokens](https://developers.tiktok.com/doc/oauth-user-access-token-management/)
- [Get User Info](https://developers.tiktok.com/doc/tiktok-api-v2-get-user-info)
