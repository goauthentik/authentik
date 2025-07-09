---
title: Integrate with Komga
sidebar_label: Komga
support_level: community
---

## What is Komga

> Komga is an open-source comic and manga server that lets users organize, read, and stream their digital comic collections with ease.
>
> -- https://komga.org/

## Preparation

The following placeholders are used in this guide:

- `komga.company` is the FQDN of the Komga installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Komga with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://komga.company/login/oauth2/code/authentik`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Komga configuration

To configure Komga, update its `application.yml` file to include the following options:

:::info
All configuration options can be found in [Komga's OAuth2 Advanced configuration documentation](https://komga.org/docs/installation/oauth2/#advanced-configuration).
:::

:::warning
You can configure Komga to use either the `sub` or `preferred_username` as the UID field under `user-name-attribute`. When using `preferred_username` as the user identifier, ensure that the [**Allow users to change username** setting](https://docs.goauthentik.io/sys-mgmt/settings#allow-users-to-change-username) is disabled to prevent authentication issues. The `sub` option uses a unique, stable identifier for the user, while `preferred_username` uses the username configured in authentik.
:::

```yml
spring:
    security:
        oauth2:
            client:
                registration:
                    authentik:
                        provider: authentik
                        client-id: <client id>
                        client-secret: <client secret>
                        client-name: authentik
                        scope: openid,email,profile
                        authorization-grant-type: authorization_code
                        redirect-uri: "{baseUrl}/{action}/oauth2/code/{registrationId}"
                provider:
                    authentik:
                        user-name-attribute: preferred_username
                        issuer-uri: https://authentik.company/application/o/<application_slug>/
```
