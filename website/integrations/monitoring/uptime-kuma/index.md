---
title: Integrate with Uptime Kuma
sidebar_label: Uptime Kuma
support_level: community
---

## What is Uptime Kuma?

> Uptime Kuma is an easy-to-use self-hosted monitoring tool.
>
> -- https://uptime.kuma.pet/

Uptime Kuma does not provide native SSO for its web UI. Use authentik as a reverse proxy in front of Uptime Kuma, and disable Uptime Kuma's built-in authentication so authentik controls access to the dashboard.

## Preparation

The following placeholders are used in this guide:

- `uptime-kuma.company` is the FQDN of the Uptime Kuma installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Uptime Kuma with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **Proxy Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **External host** to `https://uptime-kuma.company`.
        - Set **Internal host** to `http://uptime-kuma:3001`, where `uptime-kuma:3001` is the hostname and port of your Uptime Kuma instance as reached by the authentik proxy outpost.
        - Under **Advanced protocol settings**, set **Unauthenticated Paths** to the following value to allow unauthenticated access to public status pages, badges, push monitor endpoints, and their static assets:

            ```text
            ^/status(/.*)?$
            ^/status-page$
            ^/assets/.*
            ^/api/push/.*
            ^/api/badge/.*
            ^/api/status-page/.*
            ^/icon.svg$
            ^/upload/.*
            ```

        For more granular access, replace the broad status page and upload expressions with expressions that match only the published status page slug and uploaded files that should be public:

        ```text
        ^/status/<status_page_slug>$
        ^/assets/.*
        ^/api/push/.*
        ^/api/badge/.*
        ^/api/status-page/<status_page_slug>$
        ^/api/status-page/heartbeat/<status_page_slug>$
        ^/api/status-page/<status_page_slug>/manifest.json$
        ^/api/status-page/<status_page_slug>/incident-history$
        ^/api/status-page/<status_page_slug>/badge$
        ^/icon.svg$
        ^/upload/<file>$
        ```

    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure proxy outpost

The proxy provider requires an authentik proxy outpost. If you do not already have a proxy outpost, follow the [outpost documentation](/docs/add-secure-apps/outposts/) to create and deploy one.

Add the Uptime Kuma application to a proxy outpost that will serve it:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**.
3. Click the edit icon for the proxy outpost. This can be the built-in **authentik Embedded Outpost** or another proxy outpost.
4. Under **Available Applications**, select the Uptime Kuma application and move it to **Selected Applications**.
5. Click **Update** to save your changes.

## Uptime Kuma configuration

Disable Uptime Kuma's built-in authentication:

1. Log in to Uptime Kuma with the local administrator account.
2. Navigate to **Settings** > **Security**.
3. Under **Advanced**, click **Disable Auth**.
4. Confirm the change with the current password.

If Uptime Kuma is only reachable through the authentik proxy outpost, navigate to **Settings** > **Reverse Proxy** and set **Trust Proxy** to **Yes**.

## Configuration verification

To verify the login flow, open Uptime Kuma. You should be redirected to authentik before the Uptime Kuma dashboard is shown.

To verify public status pages, open a published Uptime Kuma status page in a private browser window. The status page should load without an authentik login prompt, while the dashboard should still require authentik authentication.

## Resources

- [Uptime Kuma - GitHub repository](https://github.com/louislam/uptime-kuma)
- [Uptime Kuma Wiki - Reverse Proxy](https://github.com/louislam/uptime-kuma/wiki/Reverse-Proxy)
- [Uptime Kuma Wiki - Internal API](https://github.com/louislam/uptime-kuma/wiki/Internal-API)
