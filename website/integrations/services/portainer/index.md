---
title: Integrate with Portainer
sidebar_label: Portainer
support_level: community
---

## What is Portainer

> Portainer is a powerful, GUI-based Container-as-a-Service solution that helps organizations manage and deploy cloud-native applications easily and securely.
>
> -- https://www.portainer.io/

:::note
This is based on authentik 2021.7.3 and Portainer 2.6.x-CE. Portainer 2.6 supports OAuth without additional licenses, 1.x Series requires a paid license for OAuth.
:::

## Preparation

The following placeholders are used in this guide:

- `portainer.company` is the FQDN of Portainer installation.
- `authentik.company` is the FQDN of authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Portainer with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create.)**

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>portainer.company</em>/</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Portainer configuration

In Portainer, under _Settings_, _Authentication_, Select _OAuth_ and _Custom_

- Client ID: The 'Client ID' from the authentik provider
- Client Secret: The 'Client secret' from the authentik provider
- Authorization URL: `https://authentik.company/application/o/authorize/`
- Access Token URL: `https://authentik.company/application/o/token/`
- Resource URL: `https://authentik.company/application/o/userinfo/`
- Redirect URL: `https://portainer.company/`
- Logout URL: `https://authentik.company/application/o/portainer/end-session/`
- User Identifier: `preferred_username` (Or `email` if you want to use email addresses as identifiers)
- Scopes: `email openid profile`

:::note
Portainer by default shows commas between each item in the Scopes field. Do **NOT** use commas. Use a _space_
:::

![](./port1.png)

## Notes

:::note
Portainer Reference link: https://documentation.portainer.io/v2.0/auth/oauth/
:::
