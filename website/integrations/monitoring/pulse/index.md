---
title: Integrate with Pulse
sidebar_label: Pulse
support_level: community
---

## What is Pulse

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

To support the integration of Pulse with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://pulse.company/api/oidc/callback`.
        - Select any available signing key.
        - Under **Advanced protocol settings**, add `authentik default OAuth Mapping: OpenID 'offline_access'` to the selected scopes if you want long-lived sessions backed by refresh tokens.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Pulse configuration

1. Log in to Pulse as an administrator.
2. Navigate to **Settings** > **Security** > **Single sign-on (OIDC)**.
3. Configure the following settings:
    - **Issuer URL**: `https://authentik.company/application/o/<application_slug>/`
    - **Client ID**: enter the Client ID from authentik.
    - **Client Secret**: enter the Client Secret from authentik.
    - **Redirect URL**: `https://pulse.company/api/oidc/callback`
    - **End Session URL**: `https://authentik.company/application/o/<application_slug>/end-session/`
    - **Scopes**: `openid profile email` (add `offline_access` if you added the scope mapping in authentik)
    - **Claim Mapping** _(optional)_: map `email`, `username`, and `groups` to the claims issued by authentik. Include the `groups` scope if you want to use allowed groups.
    - **Allowed Groups**, **Allowed Domains**, **Allowed Emails** _(optional)_: restrict who can sign in based on the claims Pulse receives from authentik.
4. Click **Save**.

:::info
Pulse stores refresh tokens encrypted and invalidates the session if a refresh attempt fails, so revoked access at the identity provider logs the user out on the next token refresh.
:::

### Hide local login _(optional)_

To hide the local login form and show only SSO, set `PULSE_AUTH_HIDE_LOCAL_LOGIN=true` in your environment variables, or enable **Hide local login form** in the Pulse admin UI under **Settings** > **Security** > **Authentication**. You can still access the local login by appending `?show_local=true` to the Pulse URL when needed.

## Configuration verification

To confirm that authentik is properly configured with Pulse, log out and attempt to log back in using Single Sign-On. You should be redirected to authentik for authentication and then redirected back to Pulse.

## References

- [Pulse OIDC Single Sign-On documentation](https://github.com/rcourtman/Pulse/blob/main/docs/OIDC.md)
