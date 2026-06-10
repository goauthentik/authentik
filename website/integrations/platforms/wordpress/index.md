---
title: Integrate with WordPress
sidebar_label: WordPress
support_level: community
---

## What is WordPress?

> WordPress is an open source publishing platform used to create websites, blogs, and other web content.
>
> -- https://wordpress.org/

:::info Plugin selection
There are many WordPress plugins that support SSO with different authentication protocols. This guide uses the **OpenID Connect Generic Client** plugin by Jonathan Daggerhart from the WordPress Plugin Directory.
:::

## Preparation

The following placeholders are used in this guide:

- `wp.company` is the FQDN of the WordPress installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of WordPress with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Set the **Launch URL** to `https://wp.company/wp-login.php`.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and application **slug** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://wp.company/wp-admin/admin-ajax.php?action=openid-connect-authorize`.
        - Select any available signing key.
        - Under **Advanced protocol settings** > **Scopes**, add `authentik default OAuth Mapping: OpenID 'offline_access'` to the **Selected Scopes** list.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

:::note Redirect URI
If WordPress is installed in a subdirectory, use the **Redirect URI** shown in the OpenID Connect Generic Client plugin's **Notes** section instead of the example redirect URI.
:::

## WordPress configuration

:::info
This guide assumes that you have installed and activated the **OpenID Connect Generic Client** plugin.
:::

1. Log in to WordPress as an administrator.
2. In the WordPress dashboard, navigate to **Settings** > **OpenID Connect Client**.
3. Expand **Quick Setup: Import from Discovery Document** and set the **Discovery URL** to `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`.
4. Click **Load Configuration**.
5. Review the populated endpoint settings, then configure the following settings:
    - **Client ID**: `<Client ID from authentik>`
    - **Client Secret Key**: `<Client Secret from authentik>`
    - **OpenID Scope**: `email profile openid offline_access`
6. Click **Save Changes**.

:::note Refresh tokens
The `offline_access` scope lets WordPress use refresh tokens for longer-lived sessions.
:::

:::info Optional settings
Review the WordPress plugin's optional settings for your environment. Common settings include **Link Existing Users**, **Create user if does not exist**, and **Enforce Privacy**.
:::

## Configuration verification

To confirm that authentik is properly configured with WordPress, log out of WordPress and open the WordPress integration from authentik. On the WordPress login page, click **Login with OpenID Connect** and authenticate with authentik.

## Resources

- [WordPress.org](https://wordpress.org/)
- [OpenID Connect Generic Client WordPress plugin](https://wordpress.org/plugins/daggerhart-openid-connect-generic/)
- [OpenID Connect Generic Client GitHub repository](https://github.com/oidc-wp/openid-connect-generic)
