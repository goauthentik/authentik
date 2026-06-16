---
title: Integrate with Hoop.dev
sidebar_label: Hoop.dev
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Hoop.dev?

> hoop.dev is a layer 7 gateway that masks sensitive data, blocks dangerous commands, approves risky writes, and records every session inline, before anything reaches your infrastructure.
>
> -- https://hoop.dev

## Preparation

The following placeholders are used in this guide:

- `hoop.company` is the FQDN of the Hoop.dev installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Hoop.dev with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://hoop.company/api/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Hoop.dev configuration

To support the integration of Hoop.dev with authentik, you must configure Hoop.dev to use authentik as its identity provider.

1. Log in to Hoop.dev as an administrator.
2. Navigate to **Integrations** > **Authentication**.
3. Select **Identity Provider**.
4. Under **Protocol**, select **OIDC**.
5. Under **Identity Provider**, select **Other**.
6. Configure the following settings:
    - **Client ID**: enter the **Client ID** from authentik.
    - **Client Secret**: enter the **Client Secret** from authentik.
    - **Issuer URL**: `https://authentik.company/application/o/<application_slug>/`
7. Click **Save**.

Hoop.dev automatically synchronizes authentik groups at login whenever the ID token includes the `groups` claim. To use groups for Hoop.dev access control, ensure users are added to the appropriate authentik groups before they log in.

## Configuration verification

To confirm that authentik is properly configured with Hoop.dev, open Hoop.dev, log out, and log back in. You should be redirected to authentik for authentication and then returned to Hoop.dev.

You can also verify CLI authentication by running the following commands:

```bash
hoop config create --api-url https://hoop.company
hoop login
```

## Resources

- [Hoop.dev Identity Providers overview](https://hoop.dev/docs/setup/configuration/idp/get-started)
- [Hoop.dev Environment Variables documentation](https://hoop.dev/docs/setup/configuration/env-vars)
- [Hoop.dev OIDC login callback API reference](https://hoop.dev/docs/api-reference/authentication/oidc-%7C-login-callback)
