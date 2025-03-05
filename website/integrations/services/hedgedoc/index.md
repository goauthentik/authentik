---
title: Integrate with HedgeDoc
sidebar_label: HedgeDoc
support_level: community
---

## What is HedgeDoc

> HedgeDoc lets you create real-time collaborative markdown notes.
>
> -- https://github.com/hedgedoc/hedgedoc

## Preparation

The following placeholders are used in this guide:

- `hedgedoc.company` is the FQDN of the HedgeDoc installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of HedgeDoc with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to <kbd>https://<em>hedgedoc.company</em>/auth/oauth2/callback</kbd>.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## HedgeDoc configuration

You need to set the following `env` Variables for Docker based installations.

Set the following values:

```yaml
CMD_OAUTH2_PROVIDERNAME: "authentik"
CMD_OAUTH2_CLIENT_ID: "<Client ID from above>"
CMD_OAUTH2_CLIENT_SECRET: "<Client Secret from above>"
CMD_OAUTH2_SCOPE: "openid email profile"
CMD_OAUTH2_USER_PROFILE_URL: "https://authentik.company/application/o/userinfo/"
CMD_OAUTH2_TOKEN_URL: "https://authentik.company/application/o/token/"
CMD_OAUTH2_AUTHORIZATION_URL: "https://authentik.company/application/o/authorize/"
CMD_OAUTH2_USER_PROFILE_USERNAME_ATTR: "preferred_username"
CMD_OAUTH2_USER_PROFILE_DISPLAY_NAME_ATTR: "name"
CMD_OAUTH2_USER_PROFILE_EMAIL_ATTR: "email"
```
