---
title: Integrate with Mobilizon
sidebar_label: Mobilizon
support_level: community
---

## What is Mobilizon

> Gather, organize and mobilize yourselves with a convivial, ethical, and emancipating tool. https://joinmobilizon.org
>
> -- https://joinmobilizon.org/

## Preparation

The following placeholders are used in this guide:

- `mobilizon.company` is the FQDN of the Mobilizon installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Mobilizon with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
    - Set a `Strict` redirect URI to `https://mobilizon.company/auth/keycloak/callback`.
    - Select any available signing key.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Mobilizon configuration

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
