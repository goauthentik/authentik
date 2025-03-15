---
title: Integrate with What's Up Docker
sidebar_label: What's Up Docker
support_level: community
---

## What is What's Up Docker

> What's Up Docker (WUD) is an easy-to-use tool that alerts you whenever a new version of your Docker containers is released.
>
> -- https://getwud.github.io/wud/

## Preparation

The following placeholders are used in this guide:

- `wud.company` is the FQDN of the WUD installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of What's Up Docker with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>wud.company</em>/auth/oidc/authentik/cb</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## WUD configuration

To configure WUD to use authentik, add the following values to your `.env` file:

```
WUD_AUTH_OIDC_AUTHENTIK_CLIENTID=<Your Client ID>
WUD_AUTH_OIDC_AUTHENTIK_CLIENTSECRET=<Your Client Secret>
WUD_AUTH_OIDC_AUTHENTIK_DISCOVERY=https://authentik.company/application/o/wud/.well-known/openid-configuration
WUD_AUTH_OIDC_AUTHENTIK_REDIRECT=true # Set to true to skip internal login page
```

After making these changes, restart your Docker containers to apply the new configuration.

## Configuration verification

Once completed, What's Up Docker should be successfully configured to use authentik as its Single Sign-On SSO provider.
