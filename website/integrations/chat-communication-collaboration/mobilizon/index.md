---
title: Integrate with Mobilizon
sidebar_label: Mobilizon
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Mobilizon?

> Gather, organize and mobilize yourselves with a convivial, ethical, and emancipating tool.
>
> -- https://joinmobilizon.org/

## Preparation

The following placeholders are used in this guide:

- `mobilizon.company` is the FQDN of the Mobilizon installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Mobilizon with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://mobilizon.company/auth/keycloak/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Mobilizon configuration

Edit the Mobilizon `config.exs` file and add the following settings. Replace the placeholders with values from your authentik instance.

```elixir title="config.exs"
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
  client_id: "<Client ID from authentik>",
  client_secret: "<Client Secret from authentik>",
  site: "https://authentik.company",
  authorize_url: "https://authentik.company/application/o/authorize/",
  token_url: "https://authentik.company/application/o/token/",
  userinfo_url: "https://authentik.company/application/o/userinfo/",
  token_method: :post
```

Restart the Mobilizon service for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Mobilizon, open Mobilizon, log out, then use the **authentik** button on the login page and verify that Single Sign-On succeeds.

## Resources

- [Mobilizon documentation - OAuth authentication](https://docs.mobilizon.org/3.%20System%20administration/configure/auth/#oauth)
- [ueberauth_keycloak_strategy - OAuth module settings](https://ueberauth-keycloak-strategy.hexdocs.pm/Ueberauth.Strategy.Keycloak.OAuth.html)
