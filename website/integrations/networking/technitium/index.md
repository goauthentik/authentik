---
title: Integrate with Technitium DNS
sidebar_label: Technitium DNS
support_level: community
---

## What is Technitium DNS

> Technitium DNS Server is a free, open source, cross-platform, authoritative and recursive DNS server that can be self-hosted for privacy and security, software development, and testing on small to medium-sized networks.
>
> -- https://technitium.com/dns/

## Preparation

The following placeholders are used in this guide:

- `technitium.company` is the FQDN of the Technitium DNS installation.
- `authentik.company` is the FQDN of the authentik installation.

This guide requires Technitium DNS Server version 15.0 or later.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Technitium DNS with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set **Client type** to `Confidential`.
        - Set a `Strict` redirect URI to `https://technitium.company/sso/callback`.
        - Select any available signing key.
        - Ensure that the `openid`, `email`, and `profile` scopes are selected. Remove the `email` scope if you prefer usernames to use the preferred username claim instead of the email address.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Technitium configuration

1. Log in to the Technitium web console using a local administrator account.
2. Navigate to **Administration** > **Single Sign-On (SSO)**.
3. Select **Enable Single Sign-On (SSO)**.
4. Configure the following settings:
    - **Authority (Issuer)**: `https://authentik.company/application/o/<application_slug>/`
    - **Client ID**: enter the client ID from authentik.
    - **Client Secret**: enter the client secret from authentik.
    - **Metadata Address (Optional)**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
5. Configure **SSO User Sign Up** as appropriate:
    - **Allow New User Sign Up**: enable this to allow automatic provisioning of user accounts for new SSO users.
    - **Allow Sign Up Only For Mapped Users**: enable this to restrict sign-up to users that belong to a mapped remote group. If enabled, you must configure at least one entry in the **Group Map** section, otherwise new SSO users cannot sign up.
6. _(Optional)_ Configure the **Group Map** to map authentik groups to local Technitium groups:
    - **Remote Group**: the name of the authentik group (e.g. `authentik Admins`).
    - **Local Group**: the corresponding Technitium local group (e.g. `Administrators`).

:::warning Local administrator fallback
It is strongly recommended to keep a local administrator account as a fallback. Any DNS failure could cause SSO to stop working, making it impossible for SSO-only users to log in.
:::

7. Click **Save Config** to apply the changes. The web service restarts automatically.

## Configuration verification

To confirm that authentik is properly configured with Technitium DNS, log out of Technitium. Then, navigate to the Technitium login page and click **OpenID Connect**. You should be redirected to authentik to log in, and if successful, redirected to the Technitium dashboard.

## Resources

- [Technitium DNS Server v15 release announcement](https://blog.technitium.com/2026/04/technitium-dns-server-v15-released.html)
