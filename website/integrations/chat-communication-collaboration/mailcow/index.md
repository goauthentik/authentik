---
title: Integrate with mailcow
sidebar_label: mailcow
support_level: community
---

## What is mailcow

> mailcow is a Dockerized, open-source groupware and email suite based on Docker. It relies on many well-known and long-used components, which, when combined, result in a comprehensive email server solution.
>
> -- https://mailcow.email/

:::info
In order to use authentik in mailcow, at least version `2025-03` of mailcow is required.
:::

## Preparation

The following placeholders are used in this guide:

- `mailcow.company` is the FQDN of the mailcow installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of mailcow with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID** and **Client Secret** values because they will be required later.
    - Set a `Strict` redirect URI to `https://mailcow.company`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## mailcow configuration

To configure mailcow with authentik, log in as an administrator and navigate to **System** > **Configuration**.
Then, go to **Access** > **Identity Provider** and enter the following information in the form:

- **Identity Provider**: `Generic-OIDC`
- **Authorization endpoint**: `https://authentik.company/application/o/authorize/`
- **Token endpoint**: `https://authentik.company/application/o/token/`
- **User info endpoint**: `https://authentik.company/application/o/userinfo/`
- **Client ID**: The `Client ID` from the authentik provider
- **Client Secret**: The `Client secret` from the authentik provider
- **Redirect Url**: `https://mailcow.company`
- **Client Scopes**: `openid profile email`

## Configuration verification

To confirm that authentik is properly configured with mailcow, log out and log back in via authentik.
