---
title: Integrate with Tandoor
sidebar_label: Tandoor
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Tandoor?

> Tandoor is a recipe manager for storing, searching, sharing, and planning recipes, shopping lists, and meal plans.
>
> -- https://tandoor.dev/

## Preparation

The following placeholders are used in this guide:

- `tandoor.company` is the FQDN of the Tandoor installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Tandoor with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, a slug, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** value as it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://tandoor.company/accounts/oidc/authentik/login/callback/`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Tandoor configuration

Add the following environment variables to your Tandoor configuration. Replace the placeholders with values from your authentik instance.

```env title=".env"
SOCIAL_PROVIDERS=allauth.socialaccount.providers.openid_connect
SOCIALACCOUNT_PROVIDERS='{"openid_connect":{"APPS":[{"provider_id":"authentik","name":"authentik","client_id":"<Client ID from authentik>","secret":"<Client Secret from authentik>","settings":{"server_url":"https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration"}}]}}'
```

The `provider_id` value in the `SOCIALACCOUNT_PROVIDERS` configuration is `authentik`, which matches the redirect URI path that you configured in authentik.

After the first social sign-in, use Tandoor to invite or assign the user to the appropriate recipe space. For private single-space instances, Tandoor also supports default access settings for social-login users; review the Tandoor documentation before enabling them because they apply to new social-login users.

Restart the Tandoor service for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Tandoor, log out of Tandoor, then use the **Sign in using authentik** button on the login page and verify that single sign-on succeeds.

## Resources

- [Tandoor authentication documentation](https://docs.tandoor.dev/features/authentication/)
- [Tandoor configuration documentation](https://docs.tandoor.dev/system/configuration/)
- [django-allauth OpenID Connect provider documentation](https://docs.allauth.org/en/latest/socialaccount/providers/openid_connect.html)
