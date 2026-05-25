---
title: Integrate with Personio
sidebar_label: Personio
support_level: community
---

## What is Personio?

> Personio is an all-in-one HR software designed to help small and medium-sized organizations unlock the power of people, by enabling HR to manage core processes such as recruitment, onboarding, time tracking, payroll, and performance management from a single platform.
>
> -- https://www.personio.com/

This guide was tested with Personio (SaaS) and authentik 2026.5.0.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

The callback URL on the Personio side is fixed and cannot be changed: `https://login.personio.com/login/callback`.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Personio with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application Name**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set the **Client type** to `Confidential`.
        - Set a `Strict` redirect URI to `https://login.personio.com/login/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Personio configuration

1. Log in to Personio as an administrator.
2. Navigate to **Settings** > **Security and Integrations** > **Security & Authentication**.
3. Open the **Open ID Connect (OIDC)** section and click **Configure**.
4. Under **Client Configuration**, enter the following values:
    - **Login button text**: a label for the login button on the Personio sign-in page (for example, `SSO Login`).
    - **Issuer**: `https://authentik.company/application/o/<application_slug>/`
    - **Authorization URI**: `https://authentik.company/application/o/authorize/`
    - **Token URI**: `https://authentik.company/application/o/token/`
    - **Userinfo URI**: `https://authentik.company/application/o/userinfo/` (leave the HTTP method set to `GET`)
    - **JSON Web Key Set URI**: `https://authentik.company/application/o/<application_slug>/jwks/`
    - **Scopes**: `openid,email,profile`
    - **Client ID**: the Client ID from the authentik provider.
    - **Client Secret**: the Client Secret from the authentik provider.
    - **Claim field**: `email`
5. Click **Save** and toggle the connection to **Active**.

:::info
Personio matches incoming users by the value of the configured **Claim field**. Make sure the email address returned by authentik matches the email address of the corresponding Personio employee, otherwise the SSO login will fail.
:::

## Configuration verification

To confirm that authentik is properly configured with Personio, open the Personio login page and click the SSO login button (labeled with the **Login button text** you configured above). You should be redirected to authentik to log in, then redirected back to Personio.

You can also use the **Test** button on the Personio OIDC configuration screen to validate the connection without logging out.
