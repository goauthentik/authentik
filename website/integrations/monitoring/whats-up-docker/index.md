---
title: Integrate with What's Up Docker
sidebar_label: What's Up Docker
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is What's Up Docker?

> What's Up Docker (WUD) is an easy-to-use tool that alerts you whenever a new version of your Docker containers is released.
>
> -- https://getwud.github.io/wud/

## Preparation

The following placeholders are used in this guide:

- `wud.company` is the FQDN of the WUD installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of What's Up Docker with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://wud.company/auth/oidc/authentik/cb`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## What's Up Docker configuration

To configure What's Up Docker to use authentik, add the following values to your `.env` file:

```env title=".env"
WUD_AUTH_OIDC_AUTHENTIK_CLIENTID=<Client ID from authentik>
WUD_AUTH_OIDC_AUTHENTIK_CLIENTSECRET=<Client Secret from authentik>
WUD_AUTH_OIDC_AUTHENTIK_DISCOVERY=https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration
WUD_AUTH_OIDC_AUTHENTIK_REDIRECT=true
```

The `AUTHENTIK` part of the variable names defines the WUD OIDC authentication name and must match the `authentik` segment of the redirect URI.

After making these changes, restart your WUD container to apply the new configuration. If WUD cannot determine its public URL from your reverse proxy headers, set `WUD_PUBLIC_URL` to `https://wud.company`.

## Configuration verification

To confirm that authentik is properly configured with What's Up Docker, open the integration and verify that you are redirected to authentik. If `WUD_AUTH_OIDC_AUTHENTIK_REDIRECT` is not enabled, click **Connect** on the WUD login page.

## Resources

- [WUD documentation for OpenID Connect authentication](https://getwud.github.io/wud/#/configuration/authentications/oidc/)
