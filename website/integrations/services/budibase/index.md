---
title: Integrate with Budibase
sidebar_label: Budibase
---

# Integrate with Budibase

<span class="badge badge--secondary">Support level: Community</span>

## What is Budibase

> Budibase is an open source low-code platform, and the easiest way to build internal tools that improve productivity.
>
> -- https://github.com/Budibase/budibase

## Preparation

The following placeholders are used in this guide:

- `budibase.company` is the FQDN of the Budibase installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

Create an application in authentik. Create an OAuth2/OpenID provider with the following parameters:

- Client Type: `Confidential`
- Scopes: OpenID, Email and Profile
- Signing Key: Select any available key
- Redirect URIs: `https://budibase.company/api/global/auth/oidc/callback`

Note the Client ID and Client Secret values. Create an application, using the provider you've created above.

## Budibase

In Budibase under `Auth` set the following values

- Config URL: `https://authentik.company/application/o/<Slug of the application from above>/.well-known/openid-configuration`
- Client ID: `Client ID from above`
- Client Secret: `Client Secret from above`
