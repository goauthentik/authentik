---
title: Integrate with Outline
sidebar_label: Outline
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Outline?

> Your team's knowledge base.
>
> -- https://www.getoutline.com

## Preparation

The following placeholders are used in this guide:

- `outline.company` is the FQDN of the Outline installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Outline with authentik, you need to create a scope mapping and an application/provider pair in authentik.

### Create an email verification scope mapping

Outline requires the email scope to return a value of `email_verified: True`. As of [authentik 2025.10](/docs/releases/2025/v2025.10.md#default-oauth-scope-mappings), the default behavior is to return `email_verified: False`, so a custom scope mapping is required for Outline to allow authentication.

Refer to [Email scope verification](/docs/add-secure-apps/providers/oauth2/#email-scope-verification) for instructions on how to create the required custom scope mapping.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it is required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they are required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://outline.company/auth/oidc.callback`.
        - Under **Advanced protocol settings**:
            - Set the **Subject Mode** to **Based on the User's username**.
            - Add `OAuth Mapping: OpenID 'email' with "email_verified"` to the **Selected Scopes**.
            - Remove the `authentik default OAuth Mapping: OpenID 'email'` scope.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Outline configuration

To configure Outline to use authentik, add the following variables to your Outline environment file:

```env title=".env"
OIDC_CLIENT_ID=<Client ID from authentik>
OIDC_CLIENT_SECRET=<Client Secret from authentik>
OIDC_AUTH_URI=https://authentik.company/application/o/authorize/
OIDC_TOKEN_URI=https://authentik.company/application/o/token/
OIDC_USERINFO_URI=https://authentik.company/application/o/userinfo/
OIDC_LOGOUT_URI=https://authentik.company/application/o/<application_slug>/end-session/
OIDC_DISPLAY_NAME=authentik
```

Restart Outline to apply the changes.

## Configuration verification

To confirm that authentik is properly configured with Outline, open Outline and log in with authentik.

## Resources

- [Outline Hosting - OIDC](https://docs.getoutline.com/s/hosting/doc/oidc-8CPBm6uC0I)
- [Outline Hosting - Authentication](https://docs.getoutline.com/s/hosting/doc/authentication-7ViKRmRY5o)
