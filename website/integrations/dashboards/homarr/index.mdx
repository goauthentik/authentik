---
title: Integrate with Homarr
sidebar_label: Homarr
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Homarr?

> A sleek, modern dashboard that puts all of your apps and services at your fingertips. Control everything in one convenient location. Seamlessly integrates with the apps you've added, providing you with valuable information.
>
> -- https://homarr.dev/

## Preparation

The following placeholders are used in this guide:

- `homarr.company` is the FQDN of the Homarr installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Homarr with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://homarr.company/api/auth/callback/oidc`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Configure Homarr groups _(optional)_

Homarr can synchronize group memberships from the `groups` claim that authentik sends in the OpenID `profile` scope. To use authentik groups for Homarr permissions, create groups in Homarr with names that match the authentik groups that should grant those permissions, then assign the required permissions to the Homarr groups.

## Homarr configuration

Add the following environment variables to your Homarr configuration:

```env title=".env"
AUTH_PROVIDERS=oidc
AUTH_OIDC_CLIENT_ID=<Client ID from authentik>
AUTH_OIDC_CLIENT_SECRET=<Client Secret from authentik>
AUTH_OIDC_ISSUER=https://authentik.company/application/o/<application_slug>/
AUTH_OIDC_CLIENT_NAME=authentik
```

To keep local Homarr account login available, set `AUTH_PROVIDERS=oidc,credentials`.

If you want Homarr to skip the login page and send users directly to authentik, also add `AUTH_OIDC_AUTO_LOGIN=true`.

If you are intentionally linking existing Homarr accounts by email during an OIDC provider migration, and the email addresses from your IdP are verified, also add `AUTH_OIDC_ENABLE_DANGEROUS_ACCOUNT_LINKING=true`.

Restart the Homarr service for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Homarr, open Homarr and log in with authentik. You should be redirected to authentik for authentication and then redirected back to Homarr.

## Resources

- [Homarr Single Sign On documentation](https://homarr.dev/docs/advanced/single-sign-on/)
