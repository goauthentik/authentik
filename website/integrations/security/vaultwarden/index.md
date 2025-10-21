---
title: Integrate with Vaultwarden
sidebar_label: Vaultwarden
support_level: community
---

## What is Vaultwarden

> Vaultwarden is an alternative server implementation of the Bitwarden Client API, written in Rust and compatible with official Bitwarden clients, perfect for self-hosted deployment where running the official resource-heavy service might not be ideal.
>
> -- https://github.com/dani-garcia/vaultwarden

## Preparation

The following placeholders are used in this guide:

- `vaultwarden.company` is the FQDN of the Vaultwarden installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning
Please note that this feature is currently only available on `:testing` images. More information can be found in [Vaultwarden's "Enabling SSO support using OpenID Connect"](https://github.com/dani-garcia/vaultwarden/wiki/Enabling-SSO-support-using-OpenId-Connect) documentation.
:::

## authentik configuration

To support the integration of Vaultwarden with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://vaultwarden.company/identity/connect/oidc-signin`.
        - Select any available signing key.
        - Under **Advanced protocol settings**:
            - Set **Access token validity** to more than 5 minutes.
            - Ensure the `offline_access` scope mapping is available by adding `authentik default OAuth Mapping: OpenID 'offline_access'` to the selected scopes.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Vaultwarden configuration

To configure authentik with Vaultwarden, you must add the following environment variables to your Vaultwarden deployment:

```yaml
SSO_ENABLED=true
SSO_AUTHORITY=https://authentik.company/application/o/<application_slug>/
SSO_CLIENT_ID=<client_id>
SSO_CLIENT_SECRET=<client_secret>
SSO_SCOPES="openid email profile offline_access"
SSO_ALLOW_UNKNOWN_EMAIL_VERIFICATION=false
SSO_CLIENT_CACHE_EXPIRATION=0
SSO_ONLY=false # Set to true to disable email+master password login and require SSO
SSO_SIGNUPS_MATCH_EMAIL=true # Match first SSO login to existing account by email
```

Then restart Vaultwarden to apply the changes.

## References

- [Vaultwarden Wiki - SSO using OpenID Connect](https://github.com/dani-garcia/vaultwarden/wiki/Enabling-SSO-support-using-OpenId-Connect)

## Configuration verification

To verify the integration of authentik with Vaultwarden, log out of Vaultwarden, then on the login page enter a verified email and click **Use single sign-on**.
