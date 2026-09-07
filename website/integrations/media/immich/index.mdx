---
title: Integrate with Immich
sidebar_label: Immich
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Immich?

> Immich is a self-hosted photo and video management solution.
>
> -- https://immich.app/

## Preparation

The following placeholders are used in this guide:

- `immich.company` is the FQDN of the Immich installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Immich with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add three **Redirect URIs**:
            - `Strict` `Authorization` `app.immich:///oauth-callback`
            - `Strict` `Authorization` `https://immich.company/auth/login`
            - `Strict` `Authorization` `https://immich.company/user-settings`
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
    - **Configure Launch URL** _(optional)_: set the [Launch URL](/docs/add-secure-apps/applications/#appearance) to `https://immich.company/auth/login?autoLaunch=1` to allow automatic login to Immich when clicking the application from within authentik.

3. Click **Submit** to save the new application and provider.

## Immich configuration

1. Log in to Immich as an administrator.
2. Navigate to **Administration** > **Settings** > **OAuth Authentication**.
3. Enable OAuth and configure the following settings:
    - **issuer_url**: `https://authentik.company/application/o/<application_slug>/`
    - **client_id**: enter the Client ID from authentik.
    - **client_secret**: enter the Client Secret from authentik.
4. Click **Save**.

## Configuration verification

To confirm that authentik is properly configured with Immich, open Immich and log in using OAuth. You should be redirected to authentik for authentication and then redirected back to Immich.

## Resources

- [Immich OAuth Authentication documentation](https://docs.immich.app/administration/oauth)
