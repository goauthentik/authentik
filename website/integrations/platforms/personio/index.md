---
title: Integrate with Personio
sidebar_label: Personio
support_level: community
---

## What is Personio?

> Personio is an HR software platform for managing core HR processes such as recruiting, onboarding, payroll, time tracking, and performance management.
>
> -- https://www.personio.com/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Personio with authentik, you need to create an application/provider pair in authentik.

### Copy the Personio callback URL

1. Log in to Personio as an administrator.
2. Navigate to **Settings** > **Security & integrations** > **Security & authentication**.
3. From the list of login methods, go to **Open ID Connect (OIDC)** and click **Configure**.
4. Under **Provider settings**, copy the **Callback URLs/Redirect URIs** value.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set the **Client type** to `Confidential`.
        - Add two `Strict` redirect URIs:
            - The **Callback URLs/Redirect URIs** value from Personio.
            - `https://login.personio.com/login/callback`
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Personio configuration

1. Log in to Personio as an administrator.
2. Navigate to **Settings** > **Security & integrations** > **Security & authentication**.
3. From the list of login methods, go to **Open ID Connect (OIDC)** and click **Configure**.
4. Under **Configuration**, enter the following values:
    - **Button Display Text**: `Continue with authentik`
    - **Issuer**: `https://authentik.company/application/o/<application_slug>/`
    - **Authorization URI**: `https://authentik.company/application/o/authorize/`
    - **Token URI**: `https://authentik.company/application/o/token/`
    - **Userinfo URI**: `https://authentik.company/application/o/userinfo/`
    - **JSON Web Key Set URI**: `https://authentik.company/application/o/<application_slug>/jwks/`
    - **Scopes**: `openid,email`
    - **Client ID**: the Client ID from the authentik provider.
    - **Client Secret**: the Client Secret from the authentik provider.
    - **Claim Field**: `email`
5. Submit the changes and enable the connection.

:::info User matching
Personio matches incoming users by the value of the configured **Claim Field**. Make sure each employee has an active Personio profile and that the email address returned by authentik matches the email address of the corresponding Personio employee, otherwise the SSO login will fail.
:::

## Configuration verification

To confirm that authentik is properly configured with Personio, open Personio and click **Continue with authentik**. You should be redirected to authentik to log in, then redirected back to Personio.

You can also use the **Test** button on the Personio OIDC configuration screen to validate the connection without logging out.

## Resources

- [Personio Help Center - Set up your company's authentication method](https://support.personio.de/hc/en-us/articles/360000019129-Set-up-your-company-s-authentication-method)
- [Personio Help Center - Set up single sign-on in Personio with Microsoft Entra ID using OpenID Connect](https://support.personio.de/hc/en-us/articles/4411236757521-Set-up-single-sign-on-in-Personio-with-Microsoft-Entra-ID-using-OpenID-Connect)
- [Personio Help Center - Troubleshoot SSO login issues](https://support.personio.de/hc/en-us/articles/21947067413149-Troubleshoot-SSO-login-issues)
