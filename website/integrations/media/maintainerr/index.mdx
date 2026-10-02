---
title: Integrate with Maintainerr
sidebar_label: Maintainerr
support_level: community
---

## What is Maintainerr?

> Maintainerr is a free, self-hosted tool that finds and removes unwatched or unwanted movies and shows from Plex, Jellyfin, and Emby using powerful, customizable rules.
>
> -- https://maintainerr.info/

## Preparation

The following placeholders are used in this guide:

- `maintainerr.company` is the FQDN of the Maintainerr installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Maintainerr with authentik, you need to create an application/provider pair in authentik and assign it to a proxy outpost.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **Proxy Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **External host** to `https://maintainerr.company`.
        - Set **Internal host** to `http://<maintainerr_container_name>:6246`, where `<maintainerr_container_name>:6246` is the hostname and port of your Maintainerr instance as reached by the authentik proxy outpost.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure proxy outpost

The proxy provider requires an authentik proxy outpost. If you do not already have a proxy outpost, follow the [outpost documentation](/docs/add-secure-apps/outposts/) to create and deploy one.

Add the Maintainerr application to a proxy outpost that will serve it:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Outposts**.
3. Click the edit icon for the proxy outpost. This can be the built-in **authentik Embedded Outpost** or another proxy outpost.
4. Under **Available Applications**, select the Maintainerr application and move it to **Selected Applications**.
5. Click **Update** to save your changes.

## Maintainerr configuration

Maintainerr has no authentication settings, so no SSO configuration is required in Maintainerr. The authentik proxy outpost authenticates the user before forwarding allowed requests to Maintainerr.

## Configuration verification

To confirm that authentik is properly configured with Maintainerr, open Maintainerr. You should be redirected to authentik before the Maintainerr web interface is shown.

## Resources

- [Maintainerr documentation - Security & Authentication](https://docs.maintainerr.info/security)
- [Maintainerr documentation - Reverse Proxy](https://docs.maintainerr.info/reverseproxy)
