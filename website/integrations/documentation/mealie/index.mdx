---
title: Integrate with Mealie
sidebar_label: Mealie
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Mealie?

> Mealie is a self-hosted recipe manager and meal planner. Easily add recipes by providing the URL and Mealie will automatically import the relevant data or add a family recipe with the UI editor.
>
> -- https://mealie.io/

## Preparation

The following placeholders are used in this guide:

- `mealie.company` is the FQDN of the Mealie installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Mealie with authentik, you need to create an application/provider pair and application entitlements in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** because it is required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** because they are required later.
        - Add two **Redirect URIs** of type `Strict` `Authorization`:
            - `https://mealie.company/login`
            - `https://mealie.company/login?direct=1`
        - Select any available signing key.
        - Under **Advanced protocol settings**, add **authentik default OAuth Mapping: Application Entitlements** to **Selected Scopes**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Create application entitlements

Use application entitlements to define the Mealie roles that authentik sends to Mealie.

1. Open the Mealie application that you created in the authentik Admin interface.
2. Click the **Application entitlements** tab.
3. Create two entitlements, and note their names because they are required later:
    - `mealie-users`
    - `mealie-admins`
4. Expand the `mealie-users` entitlement, click **Bind existing group/user**, and bind the users or groups that should access Mealie.
5. Expand the `mealie-admins` entitlement, click **Bind existing group/user**, and bind the users or groups that should become Mealie administrators. Users with this entitlement do not also need the `mealie-users` entitlement.

Mealie treats these values as identity provider groups, but authentik sends them from application entitlements. This keeps Mealie-specific authorization scoped to the Mealie application.

## Mealie configuration

To enable OIDC login with Mealie, update your environment variables to include the following:

```env title=".env"
OIDC_AUTH_ENABLED=true
OIDC_PROVIDER_NAME=authentik
OIDC_CONFIGURATION_URL=https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration
OIDC_CLIENT_ID=<Client ID from authentik>
OIDC_CLIENT_SECRET=<Client secret from authentik>
OIDC_GROUPS_CLAIM=entitlements
OIDC_USER_GROUP=mealie-users
OIDC_ADMIN_GROUP=mealie-admins
```

Restart the Mealie service for the changes to take effect.

### Configure login behavior _(optional)_

To redirect users directly to authentik from the Mealie login page, extend their sessions as if **Remember Me** was selected, and hide the username and password fields, add these environment variables:

```env title=".env"
OIDC_AUTO_REDIRECT=true
OIDC_REMEMBER_ME=true
ALLOW_PASSWORD_LOGIN=false
```

Restart the Mealie service for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with Mealie, open Mealie and log in via authentik.

In Mealie, click the user profile icon in the top-left corner. Then click **Members**, and confirm that users with the `mealie-admins` entitlement are **Admin** users in Mealie.

## Resources

- [Mealie OpenID Connect authentication](https://docs.mealie.io/documentation/getting-started/authentication/oidc-v2/)
- [Mealie backend configuration](https://docs.mealie.io/documentation/getting-started/installation/backend-config/#openid-connect-oidc)
