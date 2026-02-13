---
title: Integrate with Audiobookshelf
sidebar_label: Audiobookshelf
support_level: community
---

## What is Audiobookshelf

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

To support the integration of Audiobookshelf with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Add two `Strict` redirect URIs:
            - `https://audiobookshelf.company/auth/openid/callback`
            - `https://audiobookshelf.company/auth/openid/mobile-redirect`
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Audiobookshelf configuration

1. Log in to Audiobookshelf as an administrator.
2. Navigate to **Settings** > **Authentication** and enable **OpenID Connect Authentication**.
3. Configure the following settings:
    - **Issuer URL**: `https://authentik.company/application/o/<application_slug>/`
    - **Client ID**: enter the Client ID from authentik.
    - **Client Secret**: enter the Client Secret from authentik.
    - **Authorization URL**: `https://authentik.company/application/o/authorize/`
    - **Token URL**: `https://authentik.company/application/o/token/`
    - **User Info URL**: `https://authentik.company/application/o/userinfo/`
    - **JWKS URL**: `https://authentik.company/application/o/<application_slug>/jwks/`
    - **Signing Algorithm**: `RS256`
    - **Allow Mobile Redirect URLs**: `https://audiobookshelf.company/auth/openid/mobile-redirect`
    - **Match existing users by**: `username`
    - **Groups** _(optional)_: select a group to assign new users to.
    - **Auto Launch** _(optional)_: enable to automatically redirect to SSO on the login page.
    - **Auto Register** _(optional)_: enable to create new users automatically after first login.
4. Click **Save**.

:::info
To bypass SSO for troubleshooting, navigate to `https://audiobookshelf.company/login?autoLaunch=0` to access the local login form.
:::

## Configuration verification

To confirm that authentik is properly configured with Audiobookshelf, log out and attempt to log back in using OpenID Connect. You should be redirected to authentik for authentication and then redirected back to Audiobookshelf.

## References

- [Audiobookshelf OIDC Authentication documentation](https://www.audiobookshelf.org/guides/oidc_authentication/)
