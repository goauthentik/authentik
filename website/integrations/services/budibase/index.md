---
title: Integrate with Budibase
sidebar_label: Budibase
support_level: community
---

## What is Budibase

> Budibase is an open source low-code platform, and the easiest way to build internal tools that improve productivity.
>
> -- https://github.com/Budibase/budibase

## Preparation

The following placeholders are used in this guide:

- `budibase.company` is the FQDN of the Budibase installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Budibase with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>budibase.company</em>/api/global/auth/oidc/callback/</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Budibase configuration

From the main page of your Budibase installation, add the following values under the **Auth** section of the builder:

- **Config URL**: <kbd>https://<em>authentik.company</em>/application/o/<em>your-application-slug</em>/.well-known/openid-configuration</kbd>
- **Client ID**: <kbd>Client ID from authentik</kbd>
- **Client Secret**: <kbd>Client Secret from authentik</kbd>
- **Callback URL**: <kbd>https://<em>budibase.company</em>/api/global/auth/oidc/callback/</kbd>
- **Name**: <kbd>authentik</kbd>

## Resources

- [Budibase official documentation on OpenID Connect](https://docs.budibase.com/docs/openid-connect)

## Configuration verification

To confirm that authentik is properly configured with Budibase, visit your Budibase installation, and click **Sign in with authentik**.
