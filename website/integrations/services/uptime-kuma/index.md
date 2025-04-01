---
title: Integrate with Uptime Kuma
sidebar_label: Uptime Kuma
support_level: community
---

## What is Uptime Kuma

> Uptime Kuma is an easy-to-use self-hosted monitoring tool.
>
> -- https://github.com/louislam/uptime-kuma

Uptime Kuma currently supports only a single user and no native SSO solution. To still use authentik, you can work with the Proxy Outpost and a Proxy Provider.

## Preparation

The following placeholders are used in this guide:

- `uptime-kuma.company` is the FQDN of the Uptime Kuma installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Uptime Kuma with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **Proxy Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.

    - Set the **External host** to <kbd>https://<em>uptime-kuma</em>.company</kbd>.
    - Set the **Internal host** to <kbd>http://<em>uptime-kuma:3001</em></kbd> where <kbd><em>uptime-kuma:3001</em></kbd> is the hostname and port of your Uptime Kuma container.
    - Under **Advanced protocol settings**, set **Unauthenticated Paths** to the following to allow unauthenticated access to the public status page:

        ```
        ^/status/.*
        ^/assets/.*
        ^/api/push/.*
        ^/api/badge/.*
        ^/api/status-page/heartbeat/.*
        ^/icon.svg
        ^/upload/.*
        ```

        For more granular access, you can analyze requests from your status page(s) and update the following regex rules accordingly:

        ```
        ^/status/<slug>$
        ^/assets/.*
        ^/api/push/.*
        ^/api/badge/.*
        ^/api/status-page/heartbeat/<slug>$
        ^/upload/<file>$
        ```

- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Uptime Kuma configuration

Disable auth from Uptime Kuma, go to `Settings` > `Advanced` > `Disable Auth`

To access the dashboard, open `https://uptime-kuma.company/dashboard`, this will start the login with authentik. You can also set this address as the Launch URL for the application.
