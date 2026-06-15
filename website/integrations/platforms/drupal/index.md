---
title: Integrate with Drupal
sidebar_label: Drupal
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Drupal?

> Drupal is a free and open-source content management system written in PHP and
> paired with a database.
>
> -- https://en.wikipedia.org/wiki/Drupal

## Preparation

The following placeholders are used in this guide:

- `drupal.company` is the FQDN of the Drupal installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

This guide uses the [OpenID Connect / OAuth client](https://www.drupal.org/project/openid_connect) module. Install and enable this module in Drupal before continuing.

## authentik configuration

<RedirectURI20265Note />

To support the integration of Drupal with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://drupal.company/openid-connect/authentik`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Drupal configuration

1. Log in to Drupal as an administrator.
2. Navigate to **Configuration** > **People** > **OpenID Connect** and click **Generic OAuth 2.0**.
3. Configure the following settings:
    - **Name**: `authentik`
    - **Machine name**: `authentik`
    - **Client ID**: enter the **Client ID** from authentik.
    - **Client secret**: enter the **Client Secret** from authentik.
    - **Auto discover endpoints**: enable this setting.
    - **Issuer URL**: `https://authentik.company/application/o/<application_slug>/`
    - **Scopes**: `openid email profile`
4. Confirm that the **Redirect URL** shown by Drupal is `https://drupal.company/openid-connect/authentik`.
5. Click **Save**.
6. Open the **Settings** tab and configure the following settings:
    - **Override registration settings**: enable this setting if Drupal should create users who do not already have an account.
    - **OpenID buttons display in user login form**: select where the authentik login button should appear on the Drupal login form.
7. Click **Save configuration**.

## Configuration verification

To confirm that authentik is properly configured with Drupal, log out of Drupal, open the Drupal login page, and click **Log in with authentik**. You should be redirected to authentik to log in, and then redirected back to Drupal.

## Resources

- [Drupal OpenID Connect Module Documentation](https://www.drupal.org/project/openid_connect)
- [Drupal OpenID Connect client configuration documentation](https://www.drupal.org/docs/contributed-modules/openid-connect/client-configuration)
