---
title: Mobilizon
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Mobilizon

> Gather, organize and mobilize yourselves with a convivial, ethical, and emancipating tool. https://joinmobilizon.org
>
> -- https://joinmobilizon.org/

## Preparation

The following placeholders will be used:

-   `mobilizon.company` is the FQDN of the mobilizon install.
-   `authentik.company` is the FQDN of the authentik install.

## authentik Configuration

### Step 1 - OAuth2/OpenID Provider

Create a OAuth2/OpenID Provider (under _Applications/Providers_) with these settings:

-   Name : mobilizon
-   Redirect URI: `https://mobilizon.company/auth/keycloak/callback`

### Step 3 - Application

Create an application (under _Resources/Applications_) with these settings:

-   Name: Mobilizon
-   Slug: mobilizon
-   Provider: mobilizon

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
  site: "https://mobilizon.company",
  authorize_url: "https://mobilizon.company/application/o/authorize/",
  token_url: "https://mobilizon.company/application/o/token/",
  userinfo_url: "https://mobilizon.company/application/o/userinfo/",
  token_method: :post
```

Restart mobilizon.service

## Additional Resources

-   https://docs.joinmobilizon.org/administration/configure/auth/
