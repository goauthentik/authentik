---
title: Integrate with HedgeDoc
sidebar_label: HedgeDoc
support_level: community
---

## What is HedgeDoc?

> HedgeDoc lets you create real-time collaborative markdown notes.
>
> -- https://hedgedoc.org/

## Preparation

The following placeholders are used in this guide:

- `hedgedoc.company` is the FQDN of the HedgeDoc installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of HedgeDoc with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Set a `Strict` redirect URI to `https://hedgedoc.company/auth/oauth2/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.
3. Click **Submit** to save the new application and provider.

## HedgeDoc configuration

Set the following environment variables in your HedgeDoc deployment:

```yaml
CMD_OAUTH2_PROVIDERNAME: "authentik"
CMD_OAUTH2_CLIENT_ID: "<Client ID from authentik>"
CMD_OAUTH2_CLIENT_SECRET: "<Client Secret from authentik>"
CMD_OAUTH2_SCOPE: "openid email profile"
CMD_OAUTH2_USER_PROFILE_URL: "https://authentik.company/application/o/userinfo/"
CMD_OAUTH2_TOKEN_URL: "https://authentik.company/application/o/token/"
CMD_OAUTH2_AUTHORIZATION_URL: "https://authentik.company/application/o/authorize/"
CMD_OAUTH2_USER_PROFILE_ID_ATTR: "sub"
CMD_OAUTH2_USER_PROFILE_USERNAME_ATTR: "preferred_username"
CMD_OAUTH2_USER_PROFILE_DISPLAY_NAME_ATTR: "name"
CMD_OAUTH2_USER_PROFILE_EMAIL_ATTR: "email"
```

Restart HedgeDoc for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with HedgeDoc, open HedgeDoc, select the **authentik** login option, and complete the authentik sign-in flow. A successful authentication should return you to HedgeDoc as a signed-in user.

## Resources

- [HedgeDoc documentation - Configuration](https://docs.hedgedoc.org/configuration/)
- [HedgeDoc documentation - OAuth](https://docs.hedgedoc.org/guides/auth/oauth/)
