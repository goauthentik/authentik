---
title: Integrate with Mastodon
sidebar_label: Mastodon
support_level: community
---

## What is Mastodon

> Mastodon is free and open-source software for running self-hosted social networking services. It has microblogging features similar to Twitter
>
> -- https://joinmastodon.org/

## Preparation

The following placeholders are used in this guide:

- `mastodon.company` is the FQDN of the mastodon installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Mastodon with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://mastodon.company/auth/auth/openid_connect/callback`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Mastodon configuration

Configure Mastodon `OIDC_` settings by editing the `.env.production` and add the following:

:::warning
When using `preferred_username` as the user identifier, ensure that the [Allow users to change username setting](https://docs.goauthentik.io/sys-mgmt/settings#allow-users-to-change-username) is disabled to prevent authentication issues.
:::

:::info
You can configure Mastodon to use either the `sub` or `preferred_username` as the UID field under `OIDC_UID_FIELD`. The `sub` option uses a unique, stable identifier for the user, while `preferred_username` uses the username configured in authentik.
:::

```
OIDC_ENABLED=true
OIDC_DISPLAY_NAME=authentik
OIDC_DISCOVERY=true
OIDC_ISSUER=< OpenID Configuration Issuer>
OIDC_AUTH_ENDPOINT=https://authentik.company/application/o/authorize/
OIDC_SCOPE=openid,profile,email
OIDC_UID_FIELD=preferred_username
OIDC_CLIENT_ID=<Client ID>
OIDC_CLIENT_SECRET=<Client Secret>
OIDC_REDIRECT_URI=https://mastodon.company/auth/auth/openid_connect/callback
OIDC_SECURITY_ASSUME_EMAIL_IS_VERIFIED=true
```

Restart mastodon-web.service

## Additional Resources

- https://github.com/mastodon/mastodon/pull/16221
- https://forum.fedimins.net/t/sso-fuer-verschiedene-dienste/42
