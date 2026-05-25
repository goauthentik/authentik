---
title: Integrate with Dashy
sidebar_label: Dashy
support_level: community
---

## What is Dashy?

> Dashy is a self-hostable personal dashboard built for you. Includes status-checking, widgets, themes, icon packs, a UI editor and tons more.
>
> -- https://github.com/Lissy93/dashy

This guide was tested with Dashy 4.1.15 and authentik 2026.5.0.

## Preparation

The following placeholders are used in this guide:

- `dashy.company` is the FQDN of the Dashy installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Dashy with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application Name**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **slug** values because they will be required later.
        - Set the **Client type** to `Public`. Dashy runs entirely in the browser and does not store a client secret.
        - Set a `Strict` redirect URI to `https://dashy.company/`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Dashy configuration

Dashy can be configured through the web UI under **Config** > **Edit Config** or by editing `conf.yml` directly. The following steps describe the web UI flow.

1. Log in to Dashy as an administrator and click **Config** > **Edit Config**.
2. Open the **App Config** > **Auth** section.
3. Check **Enable OIDC?**.
4. Under **Oidc**:
    - Set **OIDC Endpoint** to `https://authentik.company/application/o/<application_slug>/`.
    - Set **OIDC Client Id** to the Client ID from the authentik provider.
    - Optionally, set **Admin Group** to the name of an authentik group whose members should be granted admin permissions in Dashy (for example, `Dashy-Admins`).
    - Leave **OIDC Scope** empty to use the default scopes.
5. Click **Save Changes** and reload Dashy to apply the new authentication settings.

:::info
The same settings can also be set directly in `conf.yml`:

```yaml title="conf.yml"
appConfig:
    auth:
        enableOidc: true
        oidc:
            endpoint: https://authentik.company/application/o/<application_slug>/
            clientId: <Client ID from authentik>
            adminGroup: Dashy-Admins
```

:::

## Configuration verification

To confirm that authentik is properly configured with Dashy, log out of Dashy, then reload the Dashy page and click the **Login with OIDC** button. You should be redirected to authentik to log in, then redirected back to Dashy.

## Resources

- [Dashy OIDC authentication documentation](https://dashy.to/docs/authentication/#oidc)
