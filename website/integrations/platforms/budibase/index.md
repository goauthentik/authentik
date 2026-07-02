---
title: Integrate with Budibase
sidebar_label: Budibase
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Budibase?

> Budibase is an open-source low-code platform for building internal tools and workflow applications.
>
> -- https://github.com/Budibase/budibase

## Preparation

The following placeholders are used in this guide:

- `budibase.company` is the FQDN of the Budibase installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Log in to Budibase as an administrator, open the builder, navigate to **Settings** > **Auth**, and copy the **Callback URL** displayed under **OpenID Connect**. You will use this URL when creating the authentik provider.

## authentik configuration

<RedirectURI20265Note />

To support the integration of Budibase with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.

    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` using the **Callback URL** copied from Budibase.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Budibase configuration

1. Log in to Budibase as an administrator, open the builder, and navigate to **Settings** > **Auth**.
2. Under **OpenID Connect**, set the following values:

    - **Config URL**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
    - **Client ID**: `<Client ID from authentik>`
    - **Client Secret**: `<Client Secret from authentik>`
    - **Name**: `authentik`
    - **Activated**: enabled

3. Click **Save**.

## Configuration verification

To confirm that authentik is properly configured with Budibase, open Budibase and log in with authentik.

## Resources

- [Budibase official documentation on OpenID Connect](https://docs.budibase.com/docs/openid-connect)
- [Budibase source code](https://github.com/Budibase/budibase)
