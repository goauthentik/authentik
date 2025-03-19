---
title: Integrate with Miniflux
sidebar_label: Miniflux
support_level: community
---

## What is Miniflux

> Miniflux is a minimalist and opinionated RSS feed reader.
>
> -- https://github.com/miniflux/v2

## Preparation

The following placeholders are used in this guide:

- `miniflux.company` is the FQDN of the Miniflux installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Miniflux with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name (e.g., `Miniflux`), an optional group for the type of application, the policy engine mode, and optional UI settings.

- **Choose a Provider type**: Select OAuth2/OpenID Provider as the provider type.

- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.

    - **Redirect URI**:
        - Strict: <kbd>`https://<em>miniflux.company</em>/oauth2/oidc/callback`</kbd>

- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Miniflux configuration

Add the following environment variables to your Miniflux configuration. Make sure to fill in the client ID, client secret, and OpenID Connect well-known URL from your authentik instance.

```sh
OAUTH2_PROVIDER=oidc
OAUTH2_CLIENT_ID=<Client ID from authentik>
OAUTH2_CLIENT_SECRET=<Client Secret from authentik>
OAUTH2_REDIRECT_URL=https://miniflux.company/oauth2/oidc/callback
OAUTH2_OIDC_DISCOVERY_ENDPOINT=https://authentik.company</em>/application/o/<application slug>/
OAUTH2_USER_CREATION=1
```

:::note
The trailing `.well-known/openid-configuration` is not required for `OAUTH2_OIDC_DISCOVERY_ENDPOINT`
:::

Restart the Miniflux service for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Miniflux, log out of Miniflux, locate the "Sign in with OpenID Connect" button on the login page, click on it, and ensure you can successfully log in using Single Sign-On.
