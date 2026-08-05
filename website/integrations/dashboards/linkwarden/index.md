---
title: Integrate with Linkwarden
sidebar_label: Linkwarden
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Linkwarden?

> Linkwarden is an open-source collaborative bookmark manager used to collect, organize, and preserve webpages.
>
> -- https://linkwarden.app/

## Preparation

The following placeholders are used in this guide:

- `linkwarden.company` is the FQDN of the Linkwarden installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Linkwarden with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://linkwarden.company/api/v1/auth/callback/authentik`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Linkwarden configuration

To configure Linkwarden to use authentik, add the following values to your `.env` file. Replace `<application_slug>` with the authentik application slug created earlier.

```env title=".env"
NEXTAUTH_URL=https://linkwarden.company/api/v1/auth
NEXT_PUBLIC_AUTHENTIK_ENABLED=true
AUTHENTIK_ISSUER=https://authentik.company/application/o/<application_slug>
AUTHENTIK_CLIENT_ID=<Client ID from authentik>
AUTHENTIK_CLIENT_SECRET=<Client Secret from authentik>
```

To change the login button label, set `AUTHENTIK_CUSTOM_NAME` in the same file.

After making these changes, recreate your Linkwarden containers to apply the new environment variables.

## Configuration verification

To confirm that authentik is properly configured with Linkwarden, open Linkwarden and sign in with authentik.

## Resources

- [Linkwarden SSO/OAuth integrations](https://docs.linkwarden.app/self-hosting/sso-oauth)
- [Linkwarden environment variables](https://docs.linkwarden.app/self-hosting/environment-variables)
