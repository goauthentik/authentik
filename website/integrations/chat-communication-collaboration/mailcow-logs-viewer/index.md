---
title: Integrate with mailcow Logs Viewer
sidebar_label: mailcow Logs Viewer
support_level: community
---

## What is mailcow Logs Viewer?

> A modern, self-hosted dashboard for monitoring, analyzing, and managing your mailcow mail server. Track email delivery, investigate spam, manage quarantine, detect bounce-based abuse, and validate DNS configurations, all from a single interface.
>
> -- https://github.com/ShlomiPorush/mailcow-logs-viewer

This guide was tested with mailcow Logs Viewer 2.6.1 and authentik 2026.5.0.

## Preparation

The following placeholders are used in this guide:

- `mailcow-logs-viewer.company` is the FQDN of the mailcow Logs Viewer installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of mailcow Logs Viewer with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application Name**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://mailcow-logs-viewer.company/api/auth/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## mailcow Logs Viewer configuration

To configure mailcow Logs Viewer to use authentik, add the following environment variables to your mailcow Logs Viewer deployment:

```env title="mailcow Logs Viewer environment variables"
OAUTH2_ENABLED=true
OAUTH2_PROVIDER_NAME=authentik
OAUTH2_USE_OIDC_DISCOVERY=true
OAUTH2_ISSUER_URL=https://authentik.company/application/o/<application_slug>/
OAUTH2_CLIENT_ID=<Client ID from authentik>
OAUTH2_CLIENT_SECRET=<Client Secret from authentik>
OAUTH2_REDIRECT_URI=https://mailcow-logs-viewer.company/api/auth/callback
OAUTH2_SCOPES=openid profile email
SESSION_SECRET_KEY=<output of `openssl rand -hex 32`>
SESSION_EXPIRY_HOURS=24
```

Then restart mailcow Logs Viewer to apply the changes.

:::info
The same settings can also be configured through the mailcow Logs Viewer web UI under **Settings** > **OAuth2** when `SETTINGS_EDIT_VIA_UI_ENABLED=true`. Values set through environment variables always override values set through the web UI.
:::

## Configuration verification

To confirm that authentik is properly configured with mailcow Logs Viewer, log out of mailcow Logs Viewer, then open the login page and click the **Login with authentik** button. You should be redirected to authentik to log in, then redirected back to mailcow Logs Viewer.

## Resources

- [mailcow Logs Viewer OAuth2 configuration guide](https://github.com/ShlomiPorush/mailcow-logs-viewer/blob/main/documentation/OAuth2_Configuration.md)
