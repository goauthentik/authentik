---
title: Integrate with Firezone
sidebar_label: Firezone
support_level: community
---

## What is Firezone

> Firezone is an open-source remote access platform built on WireGuard®, a modern VPN protocol that's 4-6x faster than OpenVPN.
>
> -- https://www.firezone.dev

## Preparation

The following placeholders are used in this guide:

- `firezone.company` is the FQDN of the Firezone installation.
- `authentik` is the unique ID used to generate logins for this provider.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Firezone with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create.)**

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>firezone.company</em>/auth/oidc/authentik/callback/</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Firezone configuration

- Click _Security_ under Settings
- Under _Single Sign-On_, click on _Add OpenID Connect Provider_
- Config ID: `authentik`
- Label: `Text to display on the Login button`
- Scope: `(leave default of "openid email profile")`
- Response type: `(leave default of 'code')
- Client ID: `Taken from Authentik Provider Config`
- Client Secret: `Taken from Authentik Provider Config`
- Discovery Document URI: `OpenID Configuration URL from Authentik`
- Redirect URI: `https://firezone.company/auth/oidc/<ConfigID>/callback/`
  :::note
  You should be able to leave the default Rediret URL
  :::
- Auto-create Users: Enabled in order to automatically provision users when signing in the first time.
- Click _Save_,

Although local authentication is quick and easy to get started with, you can limit attack surface by disabling local authentication altogether. For production deployments it's usually a good idea to disable local authentication and enforce MFA through authentik.

:::info
In case something goes wrong with the configuration, you can temporarily re-enable local authentication via the REST API or by following instructions from https://www.firezone.dev/docs/administer/troubleshoot/#re-enable-local-authentication-via-cli.
:::

## Additional Resources

- https://www.firezone.dev/docs/authenticate/oidc/
- https://www.firezone.dev/docs/administer/troubleshoot/#re-enable-local-authentication-via-cli
