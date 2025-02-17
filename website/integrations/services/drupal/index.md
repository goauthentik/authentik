---
title: Integrate with Drupal
sidebar_label: Drupal
---

# Integrate with Drupal

<span class="badge badge--secondary">Support level: Community</span>

## What is Drupal

> [Drupal](https://new.drupal.org/home) is a free and open-source content
> management system written in PHP and paired with a database.
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

- `drupal.ddev.site` is the FQDN of Drupal installation.
- `authentik.company` is the FQDN of Authentik installation.

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
  https://drupal.ddev.site/openid-connect/generic
- Leave everything else as-is

### Application

- Go to Applications -> Applications
  https://authentik.company/if/admin/#/core/applications
- Create an application e.g. "Drupal" and set the Provider field to the provider
  created above

### 2FA (optional)

- Go to Flows & Stages -> Flows
- Open the default-authentication-flow (click the link with the flow name, not
  the edit button)
- Go to "Stage Bindings"
- Edit default-authentication-mfa-validation
- Select "TOTP Authenticators" in "Device classes" and
  "default-authenticator-totp-setup (TOTP Authenticator Setup Stage" in
  "Configuration stages"
  ![](./drupal_2fa.png)

## Service configuration

- Go to https://drupal.ddev.site/admin/config/services/openid-connect
- Input the Client ID and Secret you noted above
- Fill out the following endpoints:
- Authorization endpoint: https://authentik.company/application/o/authorize/
- Token endpoint: https://authentik.company/application/o/token/
  if Authentik is running locally, use http://host.docker.internal:9000/application/o/token/
- UserInfo endpoint: https://authentik.company/application/o/userinfo/
  if Authentik is running locally, use http://host.docker.internal:9000/application/o/userinfo/
- Select the "Override registration settings" checkbox
- Enable the OpenID button on user login form

## Configuration verification
Once logged in for the first time, depending on your user registration settings
you may get a message saying you've successfully logged in but your account is
blocked and needs to be approved by an administrator, so unblock the user in the
usual way, and then you can log in successfully.
