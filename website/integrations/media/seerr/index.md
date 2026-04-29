---
title: Integrate with Seerr
sidebar_label: Seerr
support_level: community
---

## What is Seerr

> Seerr (previously Jellyseerr) is a free and open source application for managing requests in your media library. It integrates with media servers like Jellyfin, Plex, and Emby, and services such as Sonarr and Radarr.
>
> -- https://docs.seerr.dev/

## Preparation

- `seerr.company` is the FQDN of the Seerr installation.
- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

To support the integration of Seerr with authentik, you need to create an application/provider pair in authentik.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, a slug, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** value as it will be required later.
    - **Choose a Provider type**: OAuth2/OpenID
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and any required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Set a `Strict` redirect URI to `https://seerr.company/login`.
        - Select any available signing key.
    - **Configure Bindings** _(optional):_ you can create a [binding](https://docs.goauthentik.io/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user’s **My applications** page.

3. Click **Submit** to save the new application and provider.

## Seerr configuration

:::info
Seerr OAuth support is currently in preview, please make sure to use the `preview-new-oidc` Docker tag.
:::

1. Log in to Seerr with an administrator account.
2. Navigate to **Settings** > **Users**.
3. Toggle on **Enable OpenID Connect Sign-In** and click on the cogwheel icon next to it.
4. Click **Add OpenID Connect Provider** and configure the following settings:
    - **Provider Name**: `authentik`
    - **Logo**: `https://authentik.company/static/dist/assets/icons/icon.svg`
    - **Issuer URL**: `https://authentik.company/application/o/seerr/`
    - **Client ID**: Client ID from authentik
    - **Client Secret**: Client Secret from authentik
    - Under **Advanced Settings**:
        - **Scopes**: `openid profile email groups`
        - **Allow New Users**: Enabled
5. Click **Save Changes**.

## Configuration verification

To verify that authentik is correctly set up with Seerr, log out of Seerr and try logging back in using the authentik button. You should be redirected to authentik, and once authenticated you will be signed in to Seerr.
