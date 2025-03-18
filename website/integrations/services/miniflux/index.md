---
title: Integrate with Miniflux
sidebar_label: Miniflux
support_level: community
---

## What is Miniflux

> Miniflux is a minimalist and opinionated RSS feed reader
>
> -- [https://github.com/miniflux/v2](https://github.com/miniflux/v2)

## Preparation

The following placeholders are used in this guide:

- `miniflux.company` is the FQDN of the miniflux installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

Create an **OAuth2/OpenID Application and Provider** under **Applications** -> **Applications** via the **Create with Provider** button, using the following settings:

- Name: `miniflux`
- Redirect URIs/Origins (RegEx): `https://miniflux.company/oauth2/oidc/callback`

Everything else is up to you, just make sure to grab the client ID and the client secret!

## Miniflux configuration

Add the following to your miniflux environment `.env` file. Make sure to edit with the client ID, client secret and server URL from your Authentik instance.

```sh
OAUTH2_PROVIDER=oidc
OAUTH2_CLIENT_ID=<Client ID from Authentik>
OAUTH2_CLIENT_SECRET=<Client Secret from Authentik>
OAUTH2_REDIRECT_URL=https://miniflux.company/oauth2/oidc/callback
OAUTH2_OIDC_DISCOVERY_ENDPOINT=https://authentik.company/application/o/miniflux/
OAUTH2_USER_CREATION=1
```

Restart the Miniflux docker service for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Miniflux, logout of Miniflux and you should see a "Sign in with OpenID Connect" button on the login page. Click on this button and you should be redirected to the Authentik login page.
