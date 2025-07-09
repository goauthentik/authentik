---
title: Integrate with WordPress
sidebar_label: WordPress
support_level: community
---

## What is WordPress

> WordPress is a free and open-source content management system written in PHP and paired with a MySQL or MariaDB database. Features include a plugin architecture and a template system, referred to within WordPress as Themes
>
> -- https://en.wikipedia.org/wiki/WordPress

:::note
There are many different plugins for WordPress that allow you to setup SSO using different authentication methods. The plugin that is explained in this tutorial is "OpenID Connect Generic Client" version 3.8.5 by Jonathan Daggerhart. This plugin uses OpenID/OAUTH2 and is free without paywalls or subscriptions at the time of writing this. The plugin is available for free in the WordPress Plugin gallery.
:::

## Preparation

The following placeholders are used in this guide:

- `wp.company` is the FQDN of WordPress installation.
- `authentik.company` is the FQDN of authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of WordPress with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://wp.company/wp-admin/admin-ajax.php\?action=openid-connect-authorize`.
    - Select any available signing key.
    - Under **Advanced Protocol Settings**, add `offline_access` to the list of selected scopes.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## WordPress configuration

:::note
Assumption is being made that you have successfully downloaded and activated the required plugin "OpenID Connect Generic Client" by Jonathan Daggerhart
:::

In WordPress, under _Settings_, Select _OpenID Connect Client_

:::note
Only settings that have been modified from default have been listed.
:::

- Login Type: OpenID Connect Button on Login (This option display a button to login using OpenID as well as local WP login)
- Client ID: Client ID from step 1
- Client Secret: Client Secret from step 1
- OpenID Scope: `email profile openid offline_access`
- Login Endpoint URL: `https://authentik.company/application/o/authorize/`
- Userinfo Endpoint URL: `https://authentik.company/application/o/userinfo/`
- Token Validation Endpoint URL: `https://authentik.company/application/o/token/`
- End Session Endpoint URL: `https://authentik.company/application/o/wordpress/end-session/`

:::note
Make sure to include the _offline_access_ scope to ensure refresh tokens are generated. Otherwise your session will expire and force users to manually log in again. Refer to the [OpenID Connect Core specification](https://openid.net/specs/openid-connect-core-1_0.html#OfflineAccess) for more information.
:::

:::note
Review each setting and choose the ones that you require for your installation. Examples of popular settings are _Link Existing Users_, _Create user if does not exist_, and _Enforce Privacy_
:::

### Step 3 - authentik

In authentik, create an application which uses this provider and directly launches WordPress' backend login-screen. Optionally apply access restrictions to the application using policy bindings.

- Name: WordPress
- Slug: wordpress
- Provider: WordPress
- Launch URL: https://wp.company/wp-login.php

## Notes

:::note
OpenID Connect Generic Client Reference link: https://wordpress.org/plugins/daggerhart-openid-connect-generic/
:::
