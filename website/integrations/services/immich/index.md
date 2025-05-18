---
title: Integrate with Immich
sidebar_label: Immich
support_level: community
---

## What is Immich

> Immich is a self-hosted backup solution for photos and videos on mobile devices.
>
> -- https://immich.app/

## Preparation

The following placeholders are used in this guide:

- `https://immich.company` is the URL used to access the Immich instance.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Immich with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Add three `Strict` redirect URIs and set them to <kbd>app.immich:///oauth-callback</kbd>, <kbd>https://<em>immich.company</em>/auth/login</kbd>, and <kbd>https://<em>immich.company</em>/user-settings</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Immich configuration

Immich documentation can be found here: https://immich.app/docs/administration/oauth

1. In Immich, navigate to **Administration** > **Settings** > **OAuth Authentication**
2. Configure Immich as follows:
    - **Issuer URL**: <kbd>https://<em>authentik.company</em>/application/o/<em>application-slug</em>/</kbd>
    - **Client ID**: Enter your Client ID from authentik
    - **Client Secret**: Enter your Client Secret from authentik
    - **Scope**: `openid email profile`
