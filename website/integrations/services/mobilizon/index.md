---
title: Integrate with Mobilizon
sidebar_label: Mobilizon
---

# Integrate with Mobilizon

<span class="badge badge--secondary">Support level: Community</span>

## What is Mobilizon

> Gather, organize and mobilize yourselves with a convivial, ethical, and emancipating tool. https://joinmobilizon.org
>
> -- https://joinmobilizon.org/

## Preparation

The following placeholders are used in this guide:

- `mobilizon.company` is the FQDN of the mobilizon installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik Configuration

### Step 1 - OAuth2/OpenID Provider

Create a OAuth2/OpenID Provider (under _Applications/Providers_) with these settings:

- Name : mobilizon
- Redirect URI: `https://mobilizon.company/auth/keycloak/callback`

### Step 3 - Application

Create an application (under _Resources/Applications_) with these settings:

- Name: Mobilizon
- Slug: mobilizon
- Provider: mobilizon

## Mobilizon Setup

Configure Mobilizon settings by editing the `config.exs` and add the following:

```
config :ueberauth,
       Ueberauth,
       providers: [
         keycloak: {Ueberauth.Strategy.Keycloak, [default_scope: "openid profile email"]}
       ]

config :mobilizon, :auth,
  oauth_consumer_strategies: [
    {:keycloak, "authentik"}
  ]

config :ueberauth, Ueberauth.Strategy.Keycloak.OAuth,
  client_id: "<Client ID>",
  client_secret: "<Client Secret>",
  site: "https://authentik.company",
  authorize_url: "https://authentik.company/application/o/authorize/",
  token_url: "https://authentik.company/application/o/token/",
  userinfo_url: "https://authentik.company/application/o/userinfo/",
  token_method: :post
```

Restart mobilizon.service

## Additional Resources

- https://docs.joinmobilizon.org/administration/configure/auth/
