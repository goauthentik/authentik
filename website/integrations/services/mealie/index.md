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

## authentik configuration

To support the integration of Mealie with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Note the **Client ID**, **Client Secret**, , and **slug** values because they will be required later.
    - Create two `Strict` redirect URIs and set to `https://mealie.company/login` and `https://mealie.company/login?direct=1`.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Create the users and administrators groups

Using the authentik Admin interface, navigate to **Directory** -> **Groups** and click **Create** to create two groups, with names of your choosing, one for **Users** (ex: `mealie-users`) and one for **Admins** (ex: `mealie-admins`).

After creating the groups, select a group, navigate to the **Users** tab, and manage its members by using the **Add existing user** and **Create user** buttons as needed. An admin will need to be added as a member to both groups to function properly.

## Mealie configuration

To enable OIDC login with Mealie, update your environment variables to include the following:

```yaml showLineNumbers
OIDC_AUTH_ENABLED=true
OIDC_PROVIDER_NAME=authentik
OIDC_CONFIGURATION_URL="https://authentik.company/application/o/<slug from authentik>/.well-known/openid-configuration"
OIDC_CLIENT_ID=<Client ID from authentik>
OIDC_CLIENT_SECRET=<Client secret from authentik>
OIDC_SIGNUP_ENABLED=true
OIDC_USER_GROUP="<Your users group created in authentik>"
OIDC_ADMIN_GROUP="<Your admins group created in authentik>"
OIDC_AUTO_REDIRECT=true   # Optional: The login page will be bypassed and you will be sent directly to your Identity Provider.
OIDC_REMEMBER_ME=true     # Optional: By setting this value to true, a session will be extended as if "Remember Me" was checked.
```

Restart the Mealie service for the changes to take effect.

## Configuration verification

1. To confirm that authentik is properly configured with Mealie, log out and log back in via authentik.
2. In Mealie click on the user profile icon in the top left. Then click on **Members**, confirm the admins set in your authentik group are an **Admin** in Mealie as expected.
