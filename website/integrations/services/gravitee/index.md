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

1. Create an **OAuth2/OpenID Provider** under **Applications** > **Providers** using the following settings:
   :::note
   Only settings that have been modified from default have been listed.
   ::: - **Name**: Gravitee - **Protocol Settings**: - **Client ID**: Either create your own Client ID or use the auto-populated ID - **Client Secret**: Either create your own Client Secret or use the auto-populated secret
   :::note
   Take note of the `Client ID` and `Client Secret` as they are required when configuring Gravitee
   ::: - **Redirect URIs/Origins**: - https://gravitee.company/user/login - https://gravitee.company/console/ # Make sure to add the trailing / at the end, at the time of writing it does not work without it
   :::note
   Be sure to add the trailing `/` at the end of the `https://gravitee.company/console/` URI, at the time of writing Gravitee does not work without this.
   :::

2. Create an **Application** under **Applications** > **Applications** using the following settings:
    - **Name**: Gravitee
    - **Slug**: gravitee
    - **Provider**: Gravitee (the provider you created in step 1)
3. Open the new provider you've just created.
4. Make a note of the following URLs:
    - **Authorize URL**
    - **Token URL**
    - **Userinfo URL**
    - **Logout URL**

## Gravitee configuration

In the Gravitee Management Console, navigate to _Organizations_ (gravitee.company/console/#!/organization/settings/identities) , under **Console** > **Authentication**. Click _Add an identity provider_, select _OpenID Connect_, and fill in the following:

:::note
Only settings that have been modified from default have been listed.
:::

- **Allow portal authentication to use this identity provider**: enable this
- **Client ID**: Enter the Client ID from authentik that you noted in step 1
- **Client Secret**: Enter the Client Secret from authentik that you noted in step 1
- **Token Endpoint**: Populate this field with the **Token URL**
- **Authorize Endpoint**: Populate this field with the **Authorize URL**
- **Userinfo Endpoint**: Populate this field with the **Userinfo URL**
- **Userinfo Logout Endpoint**: Populate this field with the **Logout URL**
- **Scopes**: `email openid profile`
