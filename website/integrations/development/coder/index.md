---
title: Integrate with Coder
sidebar_label: Coder
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Coder?

> Coder is an open-source platform that provides browser-based cloud development environments, enabling developers and teams to securely write, edit, and manage code remotely without the need for local setup.
>
> -- https://coder.com

## Preparation

The following placeholders are used in this guide:

- `coder.company` is the FQDN of your Coder installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Coder with authentik, you need to create an application/provider pair in authentik.

<RedirectURI20265Note />

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://coder.company/api/v2/users/oidc/callback`.
        - Select any available signing key.
        - Under **Advanced protocol settings**, add the `authentik default OAuth Mapping: OpenID 'offline_access'` scope.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Coder configuration

To support the integration of Coder with authentik, add the following environment variables to your Coder deployment. Set `CODER_OIDC_EMAIL_DOMAIN` to one or more comma-separated email domains that are allowed to use Coder.

```env title=".env"
CODER_OIDC_ISSUER_URL="https://authentik.company/application/o/<application_slug>/"
CODER_OIDC_EMAIL_DOMAIN="acme.company,acme-corp.company"
CODER_OIDC_CLIENT_ID="<Client ID from authentik>"
CODER_OIDC_CLIENT_SECRET="<Client Secret from authentik>"
CODER_OIDC_SCOPES="openid,profile,email,offline_access"
CODER_OIDC_SIGN_IN_TEXT="Log in with authentik"
CODER_OIDC_ICON_URL="https://authentik.company/static/dist/assets/icons/icon.svg"
```

Restart Coder after changing these settings.

## Configuration verification

To confirm that authentik is properly configured with Coder, log out of Coder and log back in by clicking **Log in with authentik**.

## Resources

- [Coder OIDC authentication documentation](https://coder.com/docs/admin/users/oidc-auth/)
- [Coder OIDC refresh token documentation](https://coder.com/docs/admin/users/oidc-auth/refresh-tokens)
