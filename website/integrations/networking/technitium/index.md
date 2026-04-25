---
title: Integrate with Technitium DNS
sidebar_label: Technitium DNS
support_level: community
---

## What is Technitium DNS

> Technitium DNS Server is an open source authoritative as well as recursive DNS server that can be used for self hosting a DNS server for privacy & security. It works out-of-the-box with no or minimal configuration and provides a user friendly web console accessible using any modern web browser.
>
> -- https://technitium.com/dns/

## Preparation

The following placeholders are used in this guide:

- `technitium.company` is the FQDN of the Technitium DNS installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Technitium DNS with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name (e.g. `Technitium DNS`), an optional group, the policy engine mode, and optional UI settings.
        - **Start URL**: `https://technitium.company/`
    - **Choose a Provider type**: Select **OAuth2/OpenID Connect**.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - **Client Type**: `Confidential`
        - **Redirect URIs**: `https://technitium.company/sso/callback`
        - **Scopes**: Ensure `openid`, `email`, and `profile` are included. Remove `email` if you prefer usernames to be based on the preferred username instead of email address.
        - Note the **Client ID** and **Client Secret** for use in the Technitium configuration below.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Technitium configuration

1. Log in to the Technitium web console using a local administrator account. The default credentials are username `admin` and password `admin`.
2. Navigate to **Administration** > **Single Sign-On (SSO)**.
3. Check **Enable Single Sign-On (SSO)**.
4. Fill in the following fields:
    - **Authority (Issuer)**: `https://authentik.company/application/o/<your-app-slug>/`
    - **Client ID**: the Client ID noted from the authentik provider.
    - **Client Secret**: the Client Secret noted from the authentik provider.
    - **Metadata Address** _(optional)_: `https://authentik.company/application/o/<your-app-slug>/.well-known/openid-configuration`
5. Configure **SSO User Sign Up** as appropriate:
    - **Allow New User Sign Up**: enable this to allow automatic provisioning of user accounts for new SSO users.
    - **Allow Sign Up Only For Mapped Users**: enable this to restrict sign-up to users who belong to a mapped remote group. If enabled, you must configure at least one entry in the **Group Map** below, otherwise no SSO users will be able to log in.
6. _(Optional)_ Configure the **Group Map** to map authentik groups to local Technitium groups:
    - **Remote Group**: the name of the authentik group (e.g. `authentik Admins`).
    - **Local Group**: the corresponding Technitium local group (e.g. `Administrators`).

:::warning
It is strongly recommended to keep a local administrator account as a fallback. Any DNS failure could cause SSO to stop working, making it impossible for SSO-only users to log in.
:::

7. Click **Save Config** at the bottom of the page to apply. The web service will restart automatically.

## Configuration verification

To confirm that authentik is properly configured with Technitium DNS, log out of Technitium and log back in by clicking the SSO login option. You should be redirected to authentik and returned to the Technitium dashboard upon successful authentication.

## Resources
- [Technitium DNS Server official website](https://technitium.com/dns/)
