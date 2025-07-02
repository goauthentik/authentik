---
title: Integrate with Kanboard
sidebar_label: Kanboard
support_level: community
---

## What is Kanboard

> Kanboard is a free and open source Kanban project management software.
>
> -- https://kanboard.org

## Preparation

The following placeholders are used in this guide:

- `kanboard.company` is the FQDN of your Kanboard installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Kanboard with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Set a `Strict` redirect URI to `https://kanboard.company/oauth/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Kanboard configuration

Integrating Kanboard with authentik requires enabling the plugin system and installing the OAuth2 plugin.

### Enable plugin management

To enable plugin management through the web interface, add the following line to your Kanboard configuration file, typically located at `/var/www/app/config.php`:

```yaml
define('PLUGIN_INSTALLER', true);
```

Then, restart your server to apply the updated configuration.

### Install and configure the plugin

1. Log in to Kanboard as an administrator and navigate to your **Profile Icon** > **Settings** > **Plugins**.
2. Locate the **OAuth2** plugin in the list and click **Install**.
3. After the installation is complete, navigate to **Profile Icon** > **Settings** > **Integrations**.
4. Under **OAuth2 Authentication**, configure the following settings:

| Setting                    | Value                                                 |
| -------------------------- | ----------------------------------------------------- |
| **Callback URL**           | `https://kanboard.company/oauth/callback` (prefilled) |
| **Client ID**              | Client ID from authentik                              |
| **Client Secret**          | Client secret from authentik                          |
| **Authorize URL**          | `https://authentik.company/application/o/authorize`   |
| **Token URL**              | `https://authentik.company/application/o/token`       |
| **User API URL**           | `https://authentik.company/application/o/userinfo`    |
| **Scopes**                 | `openid profile email`                                |
| **Username Key**           | `preferred_username`                                  |
| **Name Key**               | `name`                                                |
| **Email Key**              | `email`                                               |
| **User ID Key**            | `sub`                                                 |
| **Allow Account Creation** | Toggled                                               |

5. Click **Save** to apply your configuration.

## Configuration verification

To confirm that authentik is properly configured with Kanboard, log out and attempt to log back in by clicking **OAuth2 login**.

## Resources

- [Kanboard OAuth2 plugin](https://github.com/kanboard/plugin-oauth2)
