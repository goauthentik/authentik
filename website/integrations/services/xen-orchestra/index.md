---
title: Integrate with Xen Orchestra
sidebar_label: Xen Orchestra
support_level: community
---

## What is Xen Orchestra

> Xen Orchestra provides a user friendly web interface for every Xen based hypervisor (XenServer, xcp-ng, etc.).
>
> -- https://xen-orchestra.com/

:::note
Xen Orchestra offers authentication plugins for OpenID Connect, SAML and LDAP. This guide is using the OpenID Connect plugin.
If you are using the Xen Orchestra Appliance, the OIDC Plugin should be present. If you are using Xen Orchestra compiled from sources, make sure the plugin `auth-oidc` is installed.
:::

## Preparation

The following placeholders are used in this guide:

- `xenorchestra.company` is the FQDN of the Xen Orchestra instance.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Xen Orchestra with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>xenorchestra.company</em>/signin/oidc/callback</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Xen Orchestra configuration

Xen Orchestra allows the configuration of the OpenID Connect authentication in the plugin-section.
All of the URLs mentioned below can be copied & pasted from authentik (_Applications -> Providers -> *the provider created earlier*_).

1. Navigate to Settings -> Plugins
2. Scroll to **auth-oidc** and click on the **+** icon on the right hand side.
3. Configure the auth-oidc plugin with the following configuration values:

- Set the `Auto-discovery URL` to `https://authentik.company/application/o/xenorchestra/.well-known/openid-configuration`.
- Set the `Client identifier (key)` to the Client ID from your notes.
- Set the `Client secret` to the Client Secret from your notes.
- Check the `Fill information (optional)`-Checkbox to open the advanced menu.
- Set the `Username field` to `username`
- Set the `Scopes` to `openid profile email`

4. Enable the `auth-oidc`-Plugin by toggling the switch above the configuration.
5. You should be able to login with OIDC.

:::note
The first time a user signs in, Xen Orchesta will create a new user with the same username used in authentik. If you want to map the users by their e-mail-address instead of their username, you have to set the `Username field` to `email` in the Xen Orchestra plugin configuration.
:::
