---
title: Integrate with Gravity
sidebar_label: Gravity
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Gravity?

> Gravity is a fully-replicated DNS, DHCP, and TFTP server powered by [etcd](https://etcd.io/), offering features like built-in caching, ad/privacy blocking, automatic DNS registration, and metric tracking.
>
> -- https://gravity.beryju.io/

## Preparation

The following placeholders are used in this guide:

- `gravity.company` is the FQDN of the Gravity installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::info
Gravity automatically triggers SSO authentication when configured. To prevent this behavior, log in using the following URL: `https://gravity.company/ui/?local`.
:::

:::warning Access control
Gravity grants OIDC-authenticated users administrative access. Use authentik application bindings or policies to restrict which users can access Gravity.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Gravity with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, a slug, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** value as it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://gravity.company/auth/oidc/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Gravity configuration

1. Log in to the Gravity administrative interface.
2. Navigate to **Cluster** > **Roles** and click **API**.
3. Under the **OIDC** section, configure the following values:

- **Issuer**: `https://authentik.company/application/o/<application_slug>/`
- **Client ID**: use the Client ID from authentik
- **Client Secret**: use the Client Secret from authentik
- **Redirect URL**: `https://gravity.company/auth/oidc/callback`

4. Click **Update** to save and apply your configuration.

## Configuration verification

To verify the integration with authentik, log out of Gravity and open Gravity. You should be automatically redirected to authentik.

## Resources

- [Gravity API role configuration documentation](https://gravity.beryju.io/docs/api/role_config/)
