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

- `https://audiobookshelf.company` or `https://audiobookshelf.company/audiobookshelf` is the Audiobookshelf base URL. Use the variant that matches how users reach your Audiobookshelf instance (include the path prefix if you host it under one).
- `https://authentik.company` is the FQDN of the authentik installation.

::::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
::::

## authentik configuration

To support the integration of Audiobookshelf with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair in authentik. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add the following `Strict` redirect URIs using your Audiobookshelf base URL (include any path prefix if you host Audiobookshelf under a subpath):
            - `https://audiobookshelf.company/auth/openid/callback`
            - `https://audiobookshelf.company/auth/openid/mobile-redirect`
            - Example with a prefix: `https://audiobookshelf.company/audiobookshelf/auth/openid/callback` and `https://audiobookshelf.company/audiobookshelf/auth/openid/mobile-redirect`
        - Select any available signing key.
        - If you customize scopes, include at least `openid email profile` so Audiobookshelf can retrieve user identity details.
    - **Configure Bindings** (optional): you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Audiobookshelf configuration

To support the integration of authentik with Audiobookshelf, configure OIDC in the Audiobookshelf admin UI.

1. Log in to Audiobookshelf as an administrator.
2. Navigate to **Settings** > **Authentication** and enable **OpenID Connect Authentication**.
3. In **Issuer URL**, enter `https://authentik.company/application/o/<application-slug>/` (use the slug you set when creating the provider/application in authentik). To auto-populate, use the discovery URL `https://authentik.company/application/o/<application-slug>/.well-known/openid-configuration`.
4. If discovery is not available, enter the remaining values manually:
    - **Client ID**: enter the Client ID from authentik.
    - **Client Secret**: enter the Client Secret from authentik.
    - **Issuer URL** (if not already populated): `https://authentik.company/application/o/<application-slug>/`
    - **Authorization URL**: `https://authentik.company/application/o/authorize/`
    - **Token URL**: `https://authentik.company/application/o/token/`
    - **User Info URL**: `https://authentik.company/application/o/userinfo/`
    - **JWKS URL**: `https://authentik.company/application/o/<application-slug>/jwks/`
    - **Signing Algorithm**: `RS256`
    - **Allow Mobile Redirect URLs**: add the mobile redirect URIs you configured in authentik (for example, `https://audiobookshelf.company/auth/openid/mobile-redirect` or `https://audiobookshelf.company/audiobookshelf/auth/openid/mobile-redirect`).
    - **Subfolder for Redirect URLs**: set this to match how you host Audiobookshelf (enable if you serve it under a subpath such as `/audiobookshelf`).
    - **Groups** (optional): select a group if you want Audiobookshelf to assign new users to a specific group.
    - **Match existing users by**: choose `username` (recommended); other options are valid if they fit your user data.
    - **Auto Launch**: optional; enable if you want automatic redirect to SSO on the login page.
    - **Auto Register**: optional; enable to create new users automatically after first login.
5. Save the configuration. If you need to bypass SSO for troubleshooting, navigate to `https://audiobookshelf.company/login/?autoLaunch=0` to reach the local login form.

## Configuration verification

To confirm that authentik is correctly integrated with Audiobookshelf, log out and attempt to log back in using OIDC. You should be redirected to authentik, and after successful authentication, back to Audiobookshelf.

## Resources

- [Audiobookshelf OIDC Authentication guide](https://www.audiobookshelf.org/guides/oidc_authentication/)
- [Audiobookshelf GitHub repository](https://github.com/advplyr/audiobookshelf)
