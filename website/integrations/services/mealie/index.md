---
title: Integrate with Mealie
sidebar_label: Mealie
support_level: community
---

## What is Mealie

> Mealie is a self hosted recipe manager and meal planner. Easily add recipes by providing the url and Mealie will automatically import the relevant data or add a family recipe with the UI editor.
>
> -- https://mealie.io/

## Preparation

The following placeholders are used in this guide:

- `mealie.company` is the FQDN of the Mealie installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::tip
_Optionally_, create new groups like `mealie-users` and `mealie-admin` to scope access to the mealie application.  An admin user will need to be added as a member to both groups for this application.
:::

## authentik configuration

To support the integration of _Mealie_ with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, , and **slug** values because they will be required later.
    - Create two `strict` redirect URIs and set to <kbd>https://mealie.company/login</kbd> and <kbd>https://mealie.company/login?direct=1</kbd>.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Mealie configuration

Add the following environment variables to your Mealie configuration. Make sure to fill in the Client ID, Client Secret, and Configuration URL from your authentik instance.

```yaml
OIDC_AUTH_ENABLED: true
OIDC_PROVIDER_NAME: Authentik
OIDC_CONFIGURATION_URL: "https://authentik.company/application/o/<slug from authentik>/.well-known/openid-configuration"
OIDC_CLIENT_ID: <Client ID from authentik>
OIDC_CLIENT_SECRET: <Client secret from authentik>
OIDC_SIGNUP_ENABLED: true
# Optional: If authentik groups were created to scope access set the values to the exact name of your groups.
# OIDC_USER_GROUP: "mealie-users"
# OIDC_ADMIN_GROUP: "mealie-admin"
# OIDC_AUTO_REDIRECT: true   # Optional: The login page will be bypassed an you will be sent directly to your Identity Provider.
# OIDC_REMEMBER_ME: true     # Optional: By setting this value to true, a session will be extended as if "Remember Me" was checked.
```

Restart the Mealie service for the changes to take effect.
