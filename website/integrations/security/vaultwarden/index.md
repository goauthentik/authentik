---
title: Integrate with Vaultwarden
sidebar_label: Vaultwarden
support_level: community
---

## What is Vaultwarden?

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

## authentik configuration

To support the integration of Vaultwarden with authentik, you need to create an application/provider pair in authentik.

### Create custom scope mapping

Vaultwarden requires the email scope to return either `email_verified: True` or no `email_verified` value. Because the default authentik email scope mapping returns `email_verified: False`, create a custom scope mapping for Vaultwarden.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
    - **Select type**: select **Scope Mapping**.
    - **Configure the Scope Mapping**: Provide a descriptive name (e.g. `Vaultwarden Email Scope`), and an optional description.
        - **Scope name**: `email`
        - **Expression**:

        ```python showLineNumbers
        return {
            "email": request.user.email,
            "email_verified": True
        }
        ```

3. Click **Finish** to save the property mapping.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` `Authorization` redirect URI to `https://vaultwarden.company/identity/connect/oidc-signin`.
        - Select any available signing key.
        - Under **Advanced protocol settings**:
            - Set **Access token validity** to more than 5 minutes.
            - Ensure the `offline_access` scope mapping is available by adding `authentik default OAuth Mapping: OpenID 'offline_access'` to the selected scopes.
            - Remove the `authentik default OAuth Mapping: OpenID 'email'` scope, and add the custom scope mapping you created above.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Vaultwarden configuration

To configure Vaultwarden to use authentik, add the following environment variables to your Vaultwarden deployment:

```yaml title="Vaultwarden environment variables"
DOMAIN=https://vaultwarden.company
SSO_ENABLED=true
SSO_AUTHORITY=https://authentik.company/application/o/<application_slug>/
SSO_CLIENT_ID=<Client ID from authentik>
SSO_CLIENT_SECRET=<Client Secret from authentik>
SSO_SCOPES=email profile offline_access
SSO_ALLOW_UNKNOWN_EMAIL_VERIFICATION=false
SSO_CLIENT_CACHE_EXPIRATION=0
SSO_ONLY=false # Set to true to disable email and master password login and require SSO
SSO_SIGNUPS_MATCH_EMAIL=true # Match first SSO login to an existing account by email
```

Then restart Vaultwarden to apply the changes.

## Configuration verification

To confirm that authentik is properly configured with Vaultwarden, log out of Vaultwarden, then open Vaultwarden. Enter a verified email address and click **Use single sign-on**. You should be redirected to authentik to log in, then redirected back to Vaultwarden.

## Resources

- [Vaultwarden Wiki - SSO using OpenID Connect](https://github.com/dani-garcia/vaultwarden/wiki/Enabling-SSO-support-using-OpenId-Connect)
