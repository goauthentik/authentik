---
title: Integrate with Audiobookshelf
sidebar_label: Audiobookshelf
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Audiobookshelf?

> Audiobookshelf is a self-hosted audiobook and podcast server.
>
> -- https://audiobookshelf.org/

## Preparation

The following placeholders are used in this guide:

- `audiobookshelf.company` is the FQDN of the Audiobookshelf installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Audiobookshelf with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add three **Redirect URIs**:
            - `Strict` `Authorization` `https://audiobookshelf.company/auth/openid/callback`
            - `Strict` `Authorization` `https://audiobookshelf.company/auth/openid/mobile-redirect`
            - `Strict` `Post Logout` `https://audiobookshelf.company/login`
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Audiobookshelf configuration

1. Log in to Audiobookshelf as an administrator.
2. Navigate to **Settings** > **Authentication** and enable **OpenID Connect Authentication**.
3. Configure the following settings:
    - **Issuer URL**: `https://authentik.company/application/o/<application_slug>/`
    - Click **Auto-populate** to load the provider endpoints and supported signing algorithm from authentik.
    - **Client ID**: enter the **Client ID** from authentik.
    - **Client Secret**: enter the **Client Secret** from authentik.
4. Click **Save** and restart Audiobookshelf.

### User matching and registration _(optional)_

If your Audiobookshelf usernames match the `preferred_username` value from authentik, set **Match existing users by** to `username`. This links the existing Audiobookshelf user to the authentik user after the first successful OIDC login.

Enable **Auto Register** to create Audiobookshelf users automatically when an OIDC login does not match an existing user.

### Single sign-on behavior _(optional)_

Enable **Auto Launch** to automatically redirect users from the Audiobookshelf login page to authentik. To bypass SSO for troubleshooting, open `https://audiobookshelf.company/login?autoLaunch=0`.

:::warning Local authentication
Verify that OIDC login works before disabling **Password Authentication**. If OIDC is misconfigured and local login is disabled, you must restore local authentication directly in the Audiobookshelf database.
:::

### Role and permission claims _(optional)_

Leave **Group Claim** and **Advanced Permission Claim** empty unless you have configured compatible custom claims in authentik.

If you set **Group Claim**, Audiobookshelf expects the claim to contain a list with one of `admin`, `user`, or `guest`. If no group matches, Audiobookshelf denies access.

If you set **Advanced Permission Claim**, Audiobookshelf expects the claim to contain Audiobookshelf permissions for non-admin users.

### Mobile and subfolder redirects _(optional)_

If Audiobookshelf is served from a subfolder, select the matching **Subfolder for Redirect URLs** value in Audiobookshelf. Add the displayed callback and mobile redirect URLs to the authentik provider as `Strict` `Authorization` redirect URIs.

For third-party mobile apps that use a custom redirect URI, add that URI to **Allowed Mobile Redirect URIs** in Audiobookshelf. You do not need to add third-party mobile app redirect URIs to the authentik provider.

## Configuration verification

To confirm that authentik is properly configured with Audiobookshelf, log out of Audiobookshelf. Then, open Audiobookshelf and log in using OpenID Connect. You should be redirected to authentik for authentication and then redirected back to Audiobookshelf.

## Resources

- [Audiobookshelf OpenID Connect authentication documentation](https://www.audiobookshelf.org/docs/documentation/server-management/oidc-authentication/)
