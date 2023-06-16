---
title: Wordpress
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Wordpress

From https://en.wikipedia.org/wiki/WordPress

:::note
WordPress is a free and open-source content management system written in PHP and paired with a MySQL or MariaDB database. Features include a plugin architecture and a template system, referred to within WordPress as Themes
:::

:::note
There are many different plugins for Wordpress that allow you to setup SSO using different authentication methods. The plugin that is explained in this tutorial is "OpenID Connect Generic" version 3.8.5 by daggerhart. This plugin uses OpenID/OAUTH2 and is free without paywalls or subscriptions at the time of writing this. The plugin is available for free in the Wordpress Plugin gallery.
:::

## Preparation

The following placeholders will be used:

-   `wp.company` is the FQDN of Wordpress.
-   `authentik.company` is the FQDN of authentik.

### Step 1 - authentik

In authentik, under _Providers_, create an _OAuth2/OpenID Provider_ with these settings:

:::note
Only settings that have been modified from default have been listed.
:::

**Protocol Settings**

-   Name: Wordpress
-   Client ID: Copy and Save this for Later
-   Client Secret: Copy and Save this for later
-   Redirect URIs/Origins: `https://wp.company/wp-admin/admin-ajax.php?action=openid-connect-authorize`

### Step 2 - Wordpress

:::note
Assumption is being made that you have successfully downloaded and activated the required plugin "OpenID Connect Generic" by daggerhart
:::

In Wordpress, under _Settings_, Select _OpenID Connect Client_

:::note
Only settings that have been modified from default have been listed.
:::

-   Login Type: OpenID Connect Button on Login (This option display a button to login using OpenID as well as local WP login)
-   Client ID: Client ID from step 1
-   Client Secret: Client Secret from step 1
-   OpenID Scope: `email profile openid`
-   Login Endpoint URL: `https://authentik.company/application/o/authorize/`
-   Userinfo Endpoint URL: `https://authentik.company/application/o/userinfo/`
-   Token Validation Endpoint URL: `https://authentik.company/application/o/token/`
-   End Session Endpoint URL: `https://authentik.company/application/o/wordpress/end-session/`

:::note
Review each setting and choose the ones that you require for your installation. Examples of popular settings are _Link Existing Users_, _Create user if does not exist_, and _Enforce Privacy_
:::

### Step 3 - authentik

In authentik, create an application which uses this provider and directly launches Wordpress' backend login-screen. Optionally apply access restrictions to the application using policy bindings.

-   Name: Wordpress
-   Slug: wordpress
-   Provider: wordpress
-   Launch URL: https://wp.company/wp-login.php

## Notes

:::note
OpenID Connect Generic Client Reference link: https://wordpress.org/plugins/daggerhart-openid-connect-generic/
:::
