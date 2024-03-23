---
title: Xen Orchestra
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Xen Orchestra

> Xen Orchestra provides a user friendly web interface for every Xen based hypervisor (XenServer, xcp-ng, etc.).
>
> -- https://xen-orchestra.com/

:::note
Xen Orchestra offers authentication plugins for OpenID Connect, SAML and LDAP. This guide is usind the OpenID Connect plugin.
If you are using the Xen Orchestra Appliance, the OIDC Plugin should be present. If you are using Xen Orchestra compiled from sources, make sure the plugin `auth-oidc` is installed.
:::

## Preparation

The following placeholders will be used:

-   `xenorchestra.company` is the FQDN of the Xen Orchestra instance.
-   `authentik.company` is the FQDN of the authentik install.

## authentik configuration

### 1. Provider

Under _Providers_, create an OAuth2/OpenID provider with these settings:

-   Name: Provider for XenOrchestra
-   Authorization Flow: Select one of the availible Flows.
-   Client type: Confidental
-   Redirect URIs/Origins: `https://xenorchestra.company/signin/oidc/callback`

Take note of the Client ID and the Client Secret, because we need them for the configuration of Xen Orchestra.

### 2. Application

Create an application with the following details:

-   Slug: `xenorchestra` (If you want to choose a different slug, your URLs for the Xen Orchestra Configuration may vary.)
-   Provider: Select the one we have created in Step 1
-   Set the Launch URL to `https://xenorchestra.company/`

Optionally apply access restrictions to the application.

## Xen Orchestra configuration

Xen Orchestra allows the configuration of the OpenID Connect authentication in the plugin-section.
All of the URLs mentioned below can be copied & pasted from authentik (_Applications -> Providers -> *the provider created earlier*_).

1. Navigate to Settings -> Plugins
2. Scroll to "auth-oidc" and click on the "+ Icon" on the right hand side.
3. Set the `Auto-discovery URL` to `https://authentik.company/application/o/xenorchestra/.well-known/openid-configuration`
4. Set the `Client identifier (key)` to the Client ID from your notes.
5. Set the `Client secret` to the Client Secret from your notes.
6. Check the `Fill information (optional)`-Checkbox to open the Advanced menu.
7. Set the `Authorization URL` to `https://authentik.company/application/o/authorize/`
8. Set the `Callback URL` to `https://xenorchestra.company/signin/oidc/callback`
9. Set the `Issuer` to `https://authentik.company/application/o/xenorchestra/`
10. Set the `Token URL` to `https://authentik.company/application/o/token/`
11. Set the `User info URL` to `https://authentik.company/application/o/userinfo/`
12. Set the `Username field` to `username`
13. Set the `Scopes` to `openid profile email`
14. Enable the `auth-oidc`-Plugin by toggling the switch above the configuration.
15. You should be able to login with OIDC.

:::note
You need to create the user with the according username in XenOrchestra, before you are able to login using OIDC.
:::
