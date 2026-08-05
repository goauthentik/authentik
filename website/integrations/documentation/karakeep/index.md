---
title: Integrate with Karakeep
sidebar_label: Karakeep
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Karakeep?

> A self-hostable bookmark-everything app (links, notes and images) with AI-based automatic tagging and full-text search.
>
> -- https://karakeep.app/

## Preparation

The following placeholders are used in this guide:

- `karakeep.company` is the FQDN of the Karakeep installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Karakeep with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://karakeep.company/api/auth/callback/custom`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Karakeep configuration

Karakeep uses environment variables to configure OAuth. Add the following variables to the environment file for the Karakeep `web` container:

```env title=".env"
NEXTAUTH_URL=https://karakeep.company
OAUTH_CLIENT_ID=<Client ID from authentik>
OAUTH_CLIENT_SECRET=<Client Secret from authentik>
OAUTH_WELLKNOWN_URL=https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration
OAUTH_PROVIDER_NAME=authentik
```

If Karakeep already has local accounts that should sign in through authentik with the same email address, you can also set the following variable. Only enable this setting when you trust authentik as the OAuth provider for those account email addresses.

```env title=".env"
OAUTH_ALLOW_DANGEROUS_EMAIL_ACCOUNT_LINKING=true
```

To make authentik the only login method for Karakeep, you can add the following variables:

```env title=".env"
DISABLE_PASSWORD_AUTH=true
DISABLE_SIGNUPS=true
OAUTH_AUTO_REDIRECT=true
```

Restart the Karakeep server to apply the changes.

## Configuration verification

To confirm that authentik is properly configured with Karakeep, open Karakeep and click **Sign in with authentik**. You should be redirected to authentik, then returned to Karakeep after a successful login.

## Resources

- [Karakeep Docs - Configuration](https://docs.karakeep.app/configuration/environment-variables/)
- [Karakeep source - authentication configuration](https://github.com/karakeep-app/karakeep/blob/main/apps/web/server/auth.ts)
