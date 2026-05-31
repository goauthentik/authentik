---
title: Integrate with Nexterm
sidebar_label: Nexterm
support_level: community
---

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

To support the integration of Nexterm with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://nexterm.company/api/auth/oidc/callback`.
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
    - **Client ID**: Client ID from authentik
    - **Client Secret**: Client secret from authentik
    - **Redirect URI**: `https://nexterm.company/api/auth/oidc/callback`
    - **Scope**: `openid profile email`
5. Save the provider.

:::info
The trailing slash in the **Issuer URL** is required. You can verify the exact issuer value at `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`.
:::

## Configuration verification

To verify that authentik is correctly integrated with Nexterm, log out of Nexterm and select the authentik provider on the login page. You should be redirected to your authentik instance, and after successfully authenticating, you should return to Nexterm and be logged in automatically.

## Resources

- [Nexterm OIDC Authentication documentation](https://docs.nexterm.dev/oidc)
