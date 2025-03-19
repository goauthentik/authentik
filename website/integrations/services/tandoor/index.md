---
title: Integrate with Tandoor
sidebar_label: Tandoor
support_level: community
---

## What is Tandoor

> Application for managing recipes, planning meals and building shopping lists.
>
> -- https://github.com/TandoorRecipes/recipes

## Preparation

The following placeholders are used in this guide:

- `tandoor.company` is the FQDN of the tandoor installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration
### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can create only an application, without a provider, by clicking **Create**.)

- **Application**: provide a descriptive name (e.g., `Tandoor`), an optional group for the type of application, the policy engine mode, and optional UI settings.

- **Choose a Provider type**: Select **OAuth2/OpenID Provider** as the provider type.

- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - **Redirect URI**:
        - Strict: <kbd>https://<em>tandoor.company</em>/accounts/oidc/authentik/login/callback/</kbd>

- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Tandoor configuration

Add the following environment variables to your tandoor configuration. Make sure to fill in the client ID, client secret and OpenID Connect well-known URL from your authentik instance.

```sh
SOCIAL_PROVIDERS=allauth.socialaccount.providers.openid_connect
SOCIALACCOUNT_PROVIDERS='{"openid_connect":{"APPS":[{"provider_id":"authentik","name":"authentik","client_id":"<em><Client ID from authentik></em>","secret":"<em><Client Secret from authentik></em>","settings":{"server_url":"https://<em>authentik.company</em>/application/o/<em><application slug></em>/.well-known/openid-configuration"}}]}}
'
```

Restart the Tandoor service for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Tandoor, log out of Tandoor, locate the "Sign in with authentik" button on the login page, click on it, and ensure you can successfully log in using Single Sign-On.
