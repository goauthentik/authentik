---
title: Integrate with Jellyseerr
sidebar_label: Jellyseerr
support_level: community
---

## What is Jellyseerr

> Jellyseerr is a free and open source software application for managing requests for your media library.
> It integrates with the media server of your choice: Jellyfin, Plex, and Emby.
> In addition, it integrates with your existing services, such as Sonarr, Radarr.
>
> -- https://docs.seerr.dev/

## Preparation

- `jellyseerr.company` is the FQDN of the Jellyseerr installation.
- `authentik.company` is the FQDN of the authentik installation.

## authentik configuration

The steps to configure authentik include creating an application and provider pair in authentik, obtaining the Client ID, Client Secret, and slug values, setting the redirect URI, and selecting a signing key.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name (`Jellyseerr`), a slug (`jellyseerr`), an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: OAuth2/OpenID
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and any required configurations.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://jellyseerr.company/login?provider=authentik&callback=true`.
    - Select any available signing key.
- **Configure Bindings** _(optional):_ you can create a [binding](https://docs.goauthentik.io/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user’s **My applications** page.

3. Click **Submit** to save the new application and provider.

## Jellyseerr configuration

:::info
Jellyseer OAuth support is currently in preview, please make sure to use the `preview-OIDC` docker tag.
:::

1. Log in to Jellyseerr with an administrator account and navigate to the user settings page by clicking **Settings > Users**.
2. Toggle on **Enable OpenID Connect Sign-In** and click on the cogwheel icon next to it.
3. Click **Add OpenID Connect Provider** and fill the form:
    - Provider Name: `authentik`
    - Logo: `https://cdn.jsdelivr.net/gh/selfhst/icons@main/svg/authentik.svg`
    - Issuer URL: `https://authentik.company/application/o/jellyseerr/`
    - Client ID: Client ID from provider
    - Client Secret: Client Secret from provider
    - Advanced Settings:
        - Scopes: `openid profile email groups`
        - Allow New Users: **CHECKED**
4. Click **Save Changes**.

## Configuration verification

- Open your web browser and go to: `https://jellyseerr.company`.
- Click **authentik** to log in.
- You should be redirected to authentik (following the login flow you configured). After logging in, authentik will redirect you back to `https://jellyseerr.company`.
- If you successfully return to the Jellyseerr WebGUI, the login is working correctly.
