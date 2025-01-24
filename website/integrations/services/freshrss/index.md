---
title: Integrate with FreshRSS
sidebar_label: FreshRSS
---

# FreshRSS

<span class="badge badge--secondary">Support level: Community</span>

## What is FreshRSS

> FreshRSS is a self-hosted RSS feed aggregator.
>
> -- https://github.com/FreshRSS/FreshRSS

## Preparation

The following placeholders are used in this guide:

- `freshrss.company` is the FQDN of the FreshRSS installation.
- `port` is the port on which the FreshRSS install is running (usually 443)
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

1. Create an **OAuth2/OpenID Provider** under **Applications** > **Providers** using the following settings:

    - **Name**: FreshRSS
    - **Authorization flow**: default-provider-authorization-explicit-consent
    - **Protocol Settings**:
        - **Client Type**: Confidential
        - **Client ID**: Either create your own Client ID or use the auto-populated ID
        - **Client Secret**: Either create your own Client Secret or use the auto-populated secret
          :::note
          Take note of the `Client ID` and `Client Secret`, you'll need them later.
          :::
    - **Redirect URIs/Origins**:
        - `https://freshrss.company/i/oidc/`
        - `https://freshrss.company:port/i/oidc`
    - **Signing Key**: Any of your signing keys
    - Leave everything else as default

2. Create an **Application** under **Applications** > **Applications** using the following settings:
    - **Name**: FreshRSS
    - **Slug**: freshrss
    - **Provider**: FreshRSS _(the provider you created in step 1)_
    - Leave everything else as default

## FreshRSS configuration

:::info
This integration only works with the Docker or Kubernetes install of FreshRSS, using [FreshRSS docker image](https://hub.docker.com/r/freshrss/freshrss/), on x86_64 systems and without the Alpine version of the image. More information can be found on [this issue on FreshRSS GitHub](https://github.com/FreshRSS/FreshRSS/issues/5722)
:::

Add those environment variables to your _Docker_ image :

- `OIDC_ENABLED` : `1`
- `OIDC_PROVIDER_METADATA_URL` : `https://authentik.company/application/o/<application-slug>/.well-known/openid-configuration` replacing `<application-slug>` with the slug of your created application
- `OIDC_CLIENT_ID` : the client ID of your provider
- `OIDC_CLIENT_SECRET` : the client secret of your provider
- `OIDC_X_FORWARDED_HEADERS` : `X-Forwarded-Port X-Forwarded-Proto X-Forwarded-Host`
- `OIDC_SCOPES` : `openid email profile`

Before restarting your Docker container, ensure that one of the Admin users of your FreshRSS instance has the same login as one of your Authentik user.

Restart your FreshRSS container, and login as a user that exists on both FreshRSS and your Authentik.
Navigate to _Settings_ > _Authentication_ in your FreshRSS instance, and choose as an authentication method _HTTP (for advanced users with HTTPS)_

You can find additional information on [FreshRSS documentation](https://freshrss.github.io/FreshRSS/en/admins/16_OpenID-Connect.html)
