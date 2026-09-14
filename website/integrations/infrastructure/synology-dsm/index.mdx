---
title: Integrate with Synology DSM (DiskStation Manager)
sidebar_label: Synology DSM (DiskStation Manager)
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Synology DSM?

> Synology Inc. is a Taiwanese corporation that specializes in network-attached storage (NAS) appliances. Synology's line of NAS is known as the DiskStation for desktop models, FlashStation for all-flash models, and RackStation for rack-mount models. Synology's products are distributed worldwide and localized in several languages.
>
> -- https://www.synology.com/en-global/dsm

## Preparation

The following placeholders are used in this guide:

- `synology.company` is the FQDN of the Synology DSM server.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Synology DSM with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://synology.company`.
        - Select any available signing key.
        - Under **Advanced protocol settings**, set the **Subject mode** to be based on the user's email.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Synology DSM configuration

To configure Synology DSM to utilize authentik as an OpenID Connect 1.0 Provider:

1. In the DSM Control Panel, navigate to **Domain/LDAP** > **SSO Client**.
2. Check the **Enable OpenID Connect SSO service** checkbox in the **OpenID Connect SSO Service** section.
3. Configure the following values:
    - **Profile**: `OIDC`
    - **Account type**: `Domain/LDAP/local`
    - **Name**: `authentik`
    - **Well Known URL**: copy the **OpenID Configuration URL** from the authentik provider.
    - **Application ID**: enter the **Client ID** from the authentik provider.
    - **Application Key**: enter the **Client Secret** from the authentik provider.
    - **Redirect URL**: `https://synology.company`
    - **Authorization Scope**: `openid profile email`
    - **Username Claim**: `preferred_username`

4. Save the settings.

Ensure that users exist in the selected DSM account type before they use SSO.

### Troubleshoot `not privilege` errors

**Error `not privilege`**

The login process can fail with a `not privilege` error when the SSO pop-up is blocked. Allow pop-ups for the DSM site in the browser configuration.

This error can also happen when you have multiple redirect URI entries but DSM uses only the last one during login. DSM matches the redirect URI based on the `Host` and `HTTPS` headers, so do not add `#/signin` to the redirect URI.

## Configuration verification

To confirm that authentik is properly configured with Synology DSM, log out, open Synology DSM, and log in through authentik.

## Resources

- [Synology DSM SSO Client documentation](https://kb.synology.com/en-global/DSM/help/DSM/AdminCenter/file_directory_service_sso?version=7)
