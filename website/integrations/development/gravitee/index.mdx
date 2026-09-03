---
title: Integrate with Gravitee
sidebar_label: Gravitee
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Gravitee?

> Gravitee is an API management platform used to secure, observe, and govern API, event, and AI agent interactions.
>
> -- https://www.gravitee.io/

## Preparation

The following placeholders are used in this guide:

- `gravitee.company` is the FQDN of the Gravitee installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Gravitee with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` for each Gravitee UI that will use authentik:
            - Management Console: `https://gravitee.company/console/`
            - Developer Portal: `https://gravitee.company/user/login`
        - If your Developer Portal is served from a different path, use its login route instead, such as `https://gravitee.company/classic/user/login` or `https://gravitee.company/next/log-in`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Gravitee configuration

1. Log in to the Gravitee Management Console as an administrator.
2. Navigate to **Organization** > **Console** > **Authentication**.
3. Click **+ Add an identity provider**.
4. Select **OpenID Connect** as the provider type.
5. Configure the following settings:
    - **Name**: `authentik`
    - **Allow portal authentication to use this identity provider**: enable this option if Developer Portal users should be able to log in with authentik.
    - **Client ID**: enter the Client ID from authentik.
    - **Client Secret**: enter the Client Secret from authentik.
    - **Token Endpoint**: `https://authentik.company/application/o/token/`
    - **Authorize Endpoint**: `https://authentik.company/application/o/authorize/`
    - **UserInfo Endpoint**: `https://authentik.company/application/o/userinfo/`
    - **UserInfo Logout Endpoint**: `https://authentik.company/application/o/<application_slug>/end-session/`
    - **Scopes**: `openid profile email`
    - **User profile mapping**:
        - **ID**: `sub`
        - **First name**: `given_name`
        - **Email**: `email`
6. Click **Create**.
7. Return to the identity provider list and enable **Activate Identity Provider** for the authentik provider.

## Configuration verification

To confirm that authentik is properly configured with Gravitee, open Gravitee and click the authentik login option. Verify that you are redirected to authentik for authentication and then back to Gravitee.

## Resources

- [Gravitee Documentation - OpenID Connect](https://documentation.gravitee.io/apim/configure-and-manage-the-platform/manage-organizations-and-environments/authentication/openid-connect)
- [Gravitee Documentation - Configure authentication with SSO](https://documentation.gravitee.io/apim/developer-portal/new-developer-portal/configure-authentication/configure-authentication-with-sso)
