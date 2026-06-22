---
title: Integrate with Firezone
sidebar_label: Firezone
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Firezone?

> Firezone is an open-source remote access platform built on WireGuard®, a modern VPN protocol that's 4-6x faster than OpenVPN.
>
> -- https://www.firezone.dev

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Firezone with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://app.firezone.dev/auth/oidc/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Firezone configuration

1. Log in to the Firezone admin portal as an administrator.
2. Navigate to **Settings** > **Authentication**.
3. Click **Add Provider** and select **OIDC**.
4. Configure the provider with the following values:
    - **Name**: enter a descriptive name, such as `authentik`. This name is shown to users on the sign-in page.
    - **Authentication Context**: select where users should be able to sign in with authentik.
    - **Discovery Document URI**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
    - **Client ID**: enter the client ID from authentik.
    - **Client Secret**: enter the client secret from authentik.
    - **Email Verification**: select **Proof**.
5. Confirm that the **Redirect URI** shown by Firezone is `https://app.firezone.dev/auth/oidc/callback`.
6. Click **Verify Now** and complete the authentication flow with authentik.
7. After Firezone shows the provider as verified, click **Save**.

Firezone's universal OIDC provider does not sync users or groups. Create users in Firezone before they sign in with authentik, and create any groups that you need for Firezone access policies.

## Configuration verification

To verify that authentik is correctly integrated with Firezone, open Firezone and sign in with the authentik provider. A successful login redirects you back to Firezone.

## Resources

- [Firezone Docs - SSO with OpenID Connect](https://www.firezone.dev/kb/authenticate/oidc)
- [Firezone Docs - Create Users](https://www.firezone.dev/kb/deploy/users)
- [Firezone Docs - Create Groups](https://www.firezone.dev/kb/deploy/groups)
