---
title: Integrate with Immich
sidebar_label: Immich
---

# Immich

<span class="badge badge--secondary">Support level: Community</span>

## What is Immich

> Immich is a self-hosted backup solution for photos and videos on mobile devices.
>
> -- https://immich.app/

## Preparation

The following placeholders are used in this guide:

- `https://immich.company` is the URL used to access the Immich instance.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

1. Create a new OAuth2/OpenID Provider under **Applications** > **Providers** using the following settings:
    - **Name**: Immich
    - **Authentication flow**: default-authentication-flow
    - **Authorization flow**: default-provider-authorization-explicit-consent
    - **Client type**: Confidential
    - **Client ID**: Either create your own Client ID or use the auto-populated ID
    - **Client Secret**: Either create your own Client Secret or use the auto-populated secret
      :::note
      Take note of the `Client ID` and `Client Secret` as they are required when configuring Immich.
      :::
    - **Redirect URIs/Origins (RegEx)**:
      :::note
      Please note that the following URIs are just examples. Be sure to include all of the domains / URLs that you will use to access Immich.
      :::
        - app.immich:///oauth-callback
        - https://immich.company/auth/login
        - https://immich.company/user-settings
    - **Signing Key**: authentik Self-signed Certificate
    - Leave everything else as default
2. Open the new provider you've just created.
3. Make a note of the **OpenID Configuration Issuer**.

## Immich configuration

Immich documentation can be found here: https://immich.app/docs/administration/oauth

1. In Immich, navigate to **Administration** > **Settings** > **OAuth Authentication**
2. Configure Immich as follows:
    - **Issuer URL**: Populate this field with the `OpenID Configuration Issuer`
    - **Client ID**: Enter your Client ID from authentik
    - **Client Secret**: Enter your Client Secret from authentik
    - **Scope**: `openid email profile`
