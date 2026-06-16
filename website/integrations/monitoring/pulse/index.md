---
title: Integrate with Pulse
sidebar_label: Pulse
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Pulse?

> Pulse is an open-source monitoring platform that provides real-time insight into Proxmox, Docker, and Kubernetes infrastructure.
>
> -- https://github.com/rcourtman/Pulse

## Preparation

The following placeholders are used in this guide:

- `pulse.company` is the FQDN of the Pulse installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Pulse with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because you will use it when configuring Pulse.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://pulse.company/api/oidc/callback`.
        - Select an RSA signing key so authentik signs ID tokens with RS256.
        - Under **Advanced protocol settings** > **Scopes**, add `authentik default OAuth Mapping: OpenID 'offline_access'` to the selected scopes if you want long-lived sessions backed by refresh tokens.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Pulse configuration

1. Log in to Pulse as an administrator.
2. Navigate to **Settings** > **Security** > **Single sign-on (OIDC)**.
3. Configure the following settings:
    - **Issuer URL**: `https://authentik.company/application/o/<application_slug>/`
    - **Client ID**: enter the Client ID from authentik.
    - **Client Secret**: enter the Client Secret from authentik.
    - **Redirect URL**: confirm that Pulse shows `https://pulse.company/api/oidc/callback`. If it shows a different URL, enter `https://pulse.company/api/oidc/callback`.
    - **Logout URL**: `https://authentik.company/application/o/<application_slug>/end-session/`
4. Click **Save**.

### Configure optional OIDC settings

Pulse can also be configured with access restrictions and longer-lived sessions:

- To restrict access, expand **Show advanced OIDC options** and configure **Allowed groups**, **Allowed domains**, or **Allowed email addresses**. authentik includes the user's group names in the `groups` claim of the default `profile` scope.
- To assign Pulse roles from authentik group membership, configure **Group role mappings** as `group=roleId` pairs, for example `pulse-admins=admin`. Group role mappings require Pulse Pro.
- To enable long-lived sessions, add `offline_access` to **Scopes** in Pulse if you added the `offline_access` scope mapping in authentik. Pulse stores the refresh token with the user's session and invalidates the session if token refresh fails.

### Hide local login _(optional)_

To hide the local login form and show only SSO, set `PULSE_AUTH_HIDE_LOCAL_LOGIN=true` in your environment variables, or enable **Hide local login form** in the Pulse admin UI under **Settings** > **Security** > **Authentication**. You can still access the local login by appending `?show_local=true` to the Pulse URL when needed.

## Configuration verification

To confirm that authentik is properly configured with Pulse, log out and attempt to log back in using Single Sign-On. You should be redirected to authentik for authentication and then redirected back to Pulse.

## Resources

- [Pulse OIDC Single Sign-On documentation](https://github.com/rcourtman/Pulse/blob/main/docs/OIDC.md)
- [Pulse configuration documentation](https://github.com/rcourtman/Pulse/blob/main/docs/CONFIGURATION.md)
