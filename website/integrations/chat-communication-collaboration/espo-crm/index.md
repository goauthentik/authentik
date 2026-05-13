---
title: Integrate with EspoCRM
sidebar_label: EspoCRM
support_level: community
---

## What is EspoCRM?

> EspoCRM is a CRM (customer relationship management) web application that allows users to store, visualize, and analyze their company's business-related relationships such as opportunities, people, businesses, and projects.
>
> -- https://www.espocrm.com/

:::info Scope
This guide covers OIDC login for the primary EspoCRM interface. For team mapping or portal-specific OIDC configuration, refer to EspoCRM's [OIDC documentation](https://docs.espocrm.com/administration/oidc/).
:::

## Preparation

The following placeholders are used in this guide:

- `espocrm.company` is the FQDN of the EspoCRM installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of EspoCRM with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://espocrm.company/oauth-callback.php`.
        - Select any available signing key.
        - Under **Advanced protocol settings**, set **Subject mode** to **Based on the User's username**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## EspoCRM configuration

1. Log in to EspoCRM as an administrator.
2. Navigate to **Administration** > **Authentication** and select **OIDC** as the authentication method.
3. Configure the following settings:
    - **OIDC Client ID**: enter the Client ID from authentik.
    - **OIDC Client Secret**: enter the Client Secret from authentik.
    - **OIDC Authorization Endpoint**: `https://authentik.company/application/o/authorize/`
    - **OIDC Token Endpoint**: `https://authentik.company/application/o/token/`
    - **OIDC UserInfo Endpoint**: `https://authentik.company/application/o/userinfo/`
    - **OIDC JSON Web Key Set Endpoint**: `https://authentik.company/application/o/<application_slug>/jwks/`
    - **OIDC Scopes**: select or add `openid`, `profile`, and `email`.
    - **OIDC Logout URL**: `https://authentik.company/application/o/<application_slug>/end-session/`
    - **Allow OIDC login for admin users** _(optional)_: enable this setting if EspoCRM administrators should be able to log in with OIDC.
4. Confirm that the read-only **OIDC Authorization Redirect URI** matches `https://espocrm.company/oauth-callback.php`.
5. Save the configuration.

:::info Existing Users
This configuration uses EspoCRM's username claim setting together with authentik's username-based subject mode. Existing EspoCRM users should have usernames that match their authentik usernames, unless you intentionally use a different claim mapping.
:::

## Configuration verification

To confirm that authentik is properly configured with EspoCRM, log out, open EspoCRM, click **Login**, and log back in via authentik.

## Resources

- [EspoCRM administrator documentation on OpenID Connect authentication](https://docs.espocrm.com/administration/oidc/)
