---
title: Integrate with Rancher
sidebar_label: Rancher
support_level: authentik
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Rancher?

> Rancher is a complete software stack for teams adopting containers.
>
> -- https://www.rancher.com/

## Preparation

The following placeholders are used in this guide:

- `rancher.company` is the FQDN of the Rancher installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Rancher with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - Set **Launch URL** to `https://rancher.company`.
    - Note the **Slug** because it will be required later.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID** and **Client Secret** values because they will be required later.
    - Add a **Redirect URI** of type `Strict` `Authorization` as `https://rancher.company/verify-auth`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

Rancher uses the OIDC `sub` claim as its unique user identifier. After users have logged in with this provider, keep the authentik provider's subject mode stable unless you plan to remap users in Rancher.

## Rancher configuration

1. Log in to Rancher as an administrator.
2. In the upper-left corner, click ☰ > **Users & Authentication**.
3. In the left navigation menu, click **Auth Provider**, then select **Generic OIDC**.
4. Complete the **Configure an OIDC account** form with the following values:
    - **Client ID**: enter the Client ID from authentik.
    - **Client Secret**: enter the Client Secret from authentik.
    - **Rancher URL**: `https://rancher.company/verify-auth`.
    - **Issuer**: `https://authentik.company/application/o/<application_slug>/`.
    - **Scopes**: `openid profile email`.
    - **Rancher API Host**: if this field is shown, enter `https://rancher.company`.
5. If you changed the default OIDC claim names in authentik, use Rancher's custom claim fields to map the `name`, `email`, or `groups` claims. Rancher can use authentik's default `groups` claim without additional configuration.
6. Click **Enable**. Rancher redirects you to authentik to validate the configuration.

## Configuration verification

To confirm that authentik is properly configured with Rancher, open Rancher and log in with authentik.

## Resources

- [Rancher documentation - Configure Generic OIDC](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/authentication-permissions-and-global-configuration/authentication-config/configure-generic-oidc)
