---
title: Integrate with Gravitee
sidebar_label: Gravitee
support_level: community
---

## What is Gravitee

> Gravitee.io API Management is a flexible, lightweight and blazing-fast Open Source solution that helps your organization control who, when and how users access your APIs.
>
> It offers an easy to use GUI to setup proxies for APIs, rate limiting, api keys, caching, OAUTH rules, a portal that can be opened to the public for people to subscribe to APIs, and much more.
>
> -- https://github.com/gravitee-io/gravitee-api-management

## Preparation

The following placeholders are used in this guide:

- `gravitee.company` is the FQDN of the Gravitee installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Gravitee with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Add two `Strict` redirect URI and set them to `https://gravitee.company/user/login` and `https://gravitee.company/console/`. Ensure a trailing slash is present at the end of the second redirect URI.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Gravitee configuration

In the Gravitee Management Console, navigate to _Organizations_ (gravitee.company/console/#!/organization/settings/identities) , under **Console** > **Authentication**. Click _Add an identity provider_, select _OpenID Connect_, and fill in the following:

:::note
Only settings that have been modified from default have been listed.
:::

- **Allow portal authentication to use this identity provider**: enable this
- **Client ID**: Enter the Client ID from authentik that you noted in step 1
- **Client Secret**: Enter the Client Secret from authentik that you noted in step 1
- **Token Endpoint**: `https://authentik.company/application/o/token/`
- **Authorize Endpoint**: `https://authentik.company/application/o/authorize/`
- **Userinfo Endpoint**: `https://authentik.company/application/o/userinfo/`
- **Userinfo Logout Endpoint**: `https://authentik.company/application/o/<application_slug>/end-session/`
- **Scopes**: `email openid profile`
