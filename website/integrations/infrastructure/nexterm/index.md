---
title: Integrate with Nexterm
sidebar_label: Nexterm
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Nexterm?

> Nexterm is an open-source server management platform for SSH, VNC, and RDP.
>
> -- https://nexterm.dev/

## Preparation

The following placeholders are used in this guide:

- `nexterm.company` is the FQDN of the Nexterm installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Nexterm with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://nexterm.company/api/auth/oidc/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Nexterm configuration

1. Log in to Nexterm as an administrator.
2. Navigate to **Settings** > **Authentication**.
3. Click **Add Provider**.
4. Set the following required settings:
    - **Display Name**: `authentik`
    - **Issuer URL**: `https://authentik.company/application/o/<application_slug>/`
    - **Client ID**: the Client ID from authentik
    - **Client Secret**: the Client Secret from authentik
    - **Redirect URI**: `https://nexterm.company/api/auth/oidc/callback`
5. Save the provider.

:::info Issuer URL
The trailing slash in the **Issuer URL** is required.
:::

## Configuration verification

To verify that authentik is correctly integrated with Nexterm, log out of Nexterm and select the authentik provider on the login page. You should be redirected to your authentik instance, and after successfully authenticating, you should return to Nexterm and be logged in automatically.

## Resources

- [Nexterm OIDC Authentication documentation](https://docs.nexterm.dev/oidc)
