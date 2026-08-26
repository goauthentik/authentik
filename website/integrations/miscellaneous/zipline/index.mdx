---
title: Integrate with Zipline
sidebar_label: Zipline
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Zipline?

> Zipline is a self-hostable file upload server designed for easy file sharing, supporting tools like ShareX and Flameshot, with features such as simplified setup and extensive customization options.
>
> -- https://zipline.diced.sh/

## Preparation

The following placeholders are used in this guide:

- `zipline.company` is the FQDN of the Zipline installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Zipline with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: Provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: Select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: Provide a name (or accept the auto-provided name), choose the authorization flow for this provider, and configure the following required settings:
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://zipline.company/api/auth/oauth/oidc`.
        - Select any available signing key.
        - Under **Advanced protocol settings** > **Scopes**, add `authentik default OAuth Mapping: OpenID 'offline_access'` to the **Selected Scopes** list.
    - **Configure Bindings** _(optional)_: Create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Zipline configuration

1. From the Zipline dashboard, navigate to **Administrator** > **Settings** > **Features**.

2. Enable **OAuth Registration**, then click **Save**.

3. Navigate to **Administrator** > **Settings** > **OAuth**.

4. In the **OpenID Connect** subsection, configure the following values:
    - **OIDC Client ID**: `<Client ID from authentik>`
    - **OIDC Client Secret**: `<Client Secret from authentik>`
    - **OIDC Authorize URL**: `https://authentik.company/application/o/authorize/`
    - **OIDC Token URL**: `https://authentik.company/application/o/token/`
    - **OIDC Userinfo URL**: `https://authentik.company/application/o/userinfo/`

5. Click **Save**.

## Configuration verification

To confirm that authentik is properly configured with Zipline, log out of Zipline by clicking your user icon in the top-right corner and selecting **Logout**. A new **Login with OIDC** button should appear on the login page, allowing you to sign in with authentik.

## Resources

- [Zipline documentation - OpenID Connect (OIDC)](https://zipline.diced.sh/docs/guides/oauth/oidc)
- [Zipline documentation - OAuth](https://zipline.diced.sh/docs/guides/oauth)
