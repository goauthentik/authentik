---
title: Integrate with Xen Orchestra
sidebar_label: Xen Orchestra
---

# Xen Orchestra

<span class="badge badge--secondary">Support level: Community</span>

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
This documentation lists only the settings that have been changed from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

### 1. Provider

Under _Providers_, create an OAuth2/OpenID provider with these settings:

- Name: Provider for XenOrchestra
- Authorization Flow: Select one of the available Flows.
- Client type: Confidential
- Redirect URIs/Origins: `https://xenorchestra.company/signin/oidc/callback`

Take note of the Client ID and the Client Secret, because we need them for the configuration of Xen Orchestra.

### 2. Application

Create an application with the following details:

- Slug: `xenorchestra` (If you want to choose a different slug, your URLs for the Xen Orchestra Configuration may vary.)
- Provider: Select the one we have created in Step 1
- Set the Launch URL to `https://xenorchestra.company/`

Optionally apply access restrictions to the application.

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
