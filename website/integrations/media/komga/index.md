---
title: Integrate with Komga
sidebar_label: Komga
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Komga?

> Komga is an open-source comic and manga server that lets users organize, read, and stream their digital comic collections with ease.
>
> -- https://komga.org/

## Preparation

The following placeholders are used in this guide:

- `komga.company` is the FQDN of the Komga installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Komga with authentik, you need to create an application/provider pair in authentik.

### Create an email verification scope mapping

Komga requires the email scope to return a value of `email_verified: True`. As of [authentik 2025.10](/docs/releases/2025/v2025.10.md#default-oauth-scope-mappings) the default behavior is to return `email_verified: False`, so a custom scope mapping is required for Komga to allow authentication.

Refer to [Email scope verification](/docs/add-secure-apps/providers/oauth2/#email-scope-verification) for instructions on how to create the required custom scope mapping.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://komga.company/login/oauth2/code/authentik`.
        - Select any available signing key.
        - **Advanced protocol settings** > **Scopes**:
            - Add the custom email scope mapping to the **Selected Scopes**.
            - Remove the `authentik default OAuth Mapping: OpenID 'email'` scope.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Komga configuration

To configure Komga, update its `application.yml` file to include the following options. Existing Komga users must have email addresses that match their authentik users.

:::warning User identifier
You can configure Komga to use either the `sub` or `preferred_username` as the UID field under `user-name-attribute`. When using `preferred_username` as the user identifier, ensure that the [**Allow users to change username** setting](/docs/sys-mgmt/settings#allow-users-to-change-username) is disabled to prevent authentication issues. The `sub` option uses a unique, stable identifier for the user, while `preferred_username` uses the username configured in authentik.
:::

```yaml title="application.yml"
spring:
    security:
        oauth2:
            client:
                registration:
                    authentik:
                        provider: authentik
                        client-id: <Client ID from authentik>
                        client-secret: <Client Secret from authentik>
                        client-name: authentik
                        scope: openid,email,profile
                        authorization-grant-type: authorization_code
                        redirect-uri: "{baseUrl}/{action}/oauth2/code/{registrationId}"
                provider:
                    authentik:
                        user-name-attribute: preferred_username
                        issuer-uri: https://authentik.company/application/o/<application_slug>/
```

To have Komga create users during first login, also include the following option:

```yaml title="application.yml"
komga:
    oauth2-account-creation: true
```

Restart Komga to apply the configuration.

## Configuration verification

To confirm that authentik is properly configured with Komga, open Komga and log in using authentik. You should be redirected to authentik for authentication and then redirected back to Komga as a logged-in user.

## Resources

- [Komga Social login documentation](https://komga.org/docs/installation/oauth2/)
- [Komga Configuration options documentation](https://komga.org/docs/installation/configuration/)
