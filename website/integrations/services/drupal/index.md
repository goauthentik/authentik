---
title: Integrate with Drupal
sidebar_label: Drupal
support_level: community
---

## What is Drupal

> Drupal is a free and open-source content management system written in PHP and
> paired with a database.
>
> -- https://en.wikipedia.org/wiki/Drupal

:::note
There are many different modules for Drupal that allow you to set up SSO using
different authentication methods. This tutorial uses the
[OpenID Connect / OAuth client](https://www.drupal.org/project/openid_connect)
module.
:::

## Preparation

The following placeholders are used in this guide:

- `drupal.company` is the FQDN of Drupal installation.
- `authentik.company` is the FQDN of authentik installation.

:::note
This documentation lists only the settings that you need to change from their
default values. Be aware that any changes other than those explicitly mentioned
in this guide could cause issues accessing your application.
:::


## authentik configuration

### Provider

- Go to Applications -> Providers
  https://authentik.company/if/admin/#/core/providers
- Create an OAuth2/OpenID Provider
- Set the Authentication flow to default-authentication-flow
- The Authorisation flow can be either default-provider-authorization-implicit-consent
  or default-provider-authorization-explicit-consent
- Set the Client type to "Confidential"
- Note the Cliend ID and Client Secret
- Set the Redirect URIs/Origins to your Drupal site
  https://drupal.company/openid-connect/generic
- Leave everything else as-is

### Application

- Go to Applications -> Applications
  https://authentik.company/if/admin/#/core/applications
- Create an application e.g. "Drupal" and set the Provider field to the provider
  created above

## Drupal configuration

- From the Admin Toolbar or admin page at https://drupal.company/admin go to
  **Configuration -> OpenID Connect** or directly at https://drupal.company/admin/config/services/openid-connect.
- Input the Client ID and Secret you noted above.
- Fill out the following endpoints:
  - Authorization endpoint: <kbd>https://<em>authentik.company</em>/application/o/authorize/</kbd>
  - Token endpoint: <kbd>https://<em>authentik.company</em>/application/o/token/</kbd>
  - UserInfo endpoint: <kbd>https://<em>authentik.company</em>/application/o/userinfo/</kbd>

:::info
If you are developing Drupal locally with DDEV and authentik is also running
locally, use `host.docker.internal:9000` as the hostname for the Token and UserInfo endpoints.
:::
- Select the "Override registration settings" checkbox
- Enable the OpenID button on user login form.

## Configuration verification
To confirm that authentik is properly configured with Drupal, log out from the
Admin Toolbar link under your username, or go directly to
https://drupal.company/user/logout, and log back in via authentik at https://drupal.company/user/login.

After logging in for the first time, if your user registration settings do not
allow new users to be created then you will get a message saying you've
successfully logged in but your account is blocked and needs to be approved by
an administrator. Individual accounts can be unblocked at https://drupal.company/admin/people,
and the user registration settings can be changed at https://drupal.company/admin/config/people/accounts.
