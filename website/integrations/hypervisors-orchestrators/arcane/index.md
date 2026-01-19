---
title: Integrate with Arcane
sidebar_label: Arcane
support_level: community
---

## What is Arcane

> Modern Docker Management, Designed for Everyone. 
>
> -- https://github.com/getarcaneapp/arcane

## Preparation

The following placeholders are used in this guide:

- `arcane.company` is the FQDN of the Arcane installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Arcane with authentik, you need to create an application/provider pair in authentik.

### Create custom scope mapping

Arcane either requires the email scope to return a `true` value for whether the email address is verified, if account merge is enabled. As of [authentik 2025.10](https://docs.goauthentik.io/releases/2025.10/#default-oauth-scope-mappings) the default behavior is to return `email_verified: False`, so a custom scope mapping is required for Arcane to allow authentication.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
    - **Select type**: select **Scope Mapping**.
    - **Configure the Scope Mapping**: Provide a descriptive name (e.g. `Arcane Email Scope`), and an optional description.
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
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://arcane.company/auth/oidc/callback`.
        - Select any available signing key.
        - Under **Advanced protocol settings**:
            - Remove the `authentik default OAuth Mapping: OpenID 'email'` scope, and add the custom scope mapping you created above.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Arcane configuration

To configure authentik with Arcane, you must add the following environment variables to your Arcane deployment:

```yaml
OIDC_ENABLED=true
OIDC_CLIENT_ID=<client_id>
OIDC_CLIENT_SECRET=<client_secret>
OIDC_ISSUER_URL=https://authentik.company/application/o/<application_slug>/
OIDC_MERGE_ACCOUNTS=true # Match first SSO login to existing account by email
OIDC_SCOPES="openid email profile"
```

Then restart Arcane to apply the changes.

## References

- [Arcane Docs - OIDC Single Sign-On](https://getarcane.app/docs/configuration/sso)

## Configuration verification

To verify the integration of authentik with Arcane, log out of Arcane, then on the login page select **Sign in with OIDC Provider**.
