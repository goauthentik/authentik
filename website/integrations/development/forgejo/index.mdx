---
title: Integrate with Forgejo
sidebar_label: Forgejo
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Forgejo?

> Forgejo is a lightweight, self-hosted alternative to GitHub/GitLab, with a strong emphasis on community governance and open development.
>
> -- https://forgejo.org/

## Preparation

The following placeholders are used in this guide:

- `forgejo.company` is the FQDN of the Forgejo installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Forgejo with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://forgejo.company/user/oauth2/authentik/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Forgejo configuration

1. Log in to Forgejo as an administrator, then click your profile icon in the top-right corner and select **Site Administration**.
2. Select the **Authentication Sources** tab and then click on **Add Authentication Source**.
3. Set the following required configurations:
    - **Authentication Name**: `authentik`. This value must match the name used in the **Redirect URI** in the previous section.
    - **OAuth2 Provider**: select **OpenID Connect**.
    - **Client ID (Key)**: enter the **Client ID** from authentik.
    - **Client Secret**: enter the **Client Secret** from authentik.
    - **Icon URL**: `https://authentik.company/static/dist/assets/icons/icon.png`
    - **OpenID Connect Auto Discovery URL**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
    - **Additional Scopes**: `email profile`

4. Click **Add Authentication Source**.

### Enable automatic user registration _(optional)_

If Forgejo should create user accounts after a successful authentik login, enable OAuth2 auto-registration in the Forgejo configuration:

```ini title="app.ini"
[oauth2_client]
ENABLE_AUTO_REGISTRATION = true
```

Restart Forgejo after changing its configuration file.

### Configure permissions _(optional)_

Optionally, application entitlements and property mappings can be created to manage user permissions in Forgejo.

#### Create application entitlements

The following application entitlements will be created:

- `gituser`: normal Forgejo users.
- `gitadmin`: Forgejo users with administrative permissions.
- `gitrestricted`: restricted Forgejo users.

:::info Entitlement assignment is required
Users who are not assigned any of these entitlements will be denied login access. Users assigned the `gitadmin` entitlement will have full administrative privileges, while users assigned the `gitrestricted` entitlement will have limited access.
:::

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and open the Forgejo application.
3. Click the **Application entitlements** tab.
4. Click **New Entitlement**, set the name to `gituser`, and then click **Create**.
5. Repeat step 4 to create two additional entitlements named `gitadmin` and `gitrestricted`.
6. Open an entitlement and bind the users or groups that need Forgejo access to it.
7. Repeat step 6 for the two additional entitlements.

#### Create custom property mapping

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **Scope Mapping** with the following configurations:
    - **Name**: Choose a descriptive name (e.g. `authentik forgejo OAuth Mapping: OpenID 'forgejo'`)
    - **Scope name**: `forgejo`
    - **Expression**:

    ```python showLineNumbers
    entitlement_names = {
        entitlement.name
        for entitlement in request.user.app_entitlements(provider.application)
    }
    forgejo_claims = {}

    if "gituser" in entitlement_names:
        forgejo_claims["forgejo"] = "user"
    if "gitadmin" in entitlement_names:
        forgejo_claims["forgejo"] = "admin"
    if "gitrestricted" in entitlement_names:
        forgejo_claims["forgejo"] = "restricted"

    return forgejo_claims
    ```

3. Click **Finish**.

#### Add the custom property mapping to the provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the **Edit** icon of the Forgejo provider.
3. Under **Advanced protocol settings** > **Scopes**, add the following scope to **Selected Scopes**:
    - `authentik forgejo OAuth Mapping: OpenID 'forgejo'`

4. Click **Update**.

#### Configure Forgejo to use the new claims

1. Log in to Forgejo as an administrator. Click your profile icon in the top-right corner, and then click **Site Administration**.
2. Select the **Authentication Sources** tab and edit the **authentik** Authentication Source.
3. Set the following configurations:
    - **Additional Scopes**: `email profile forgejo`
    - **Required Claim Name**: `forgejo`
    - **Claim name providing group names for this source. (Optional)**: `forgejo`
    - **Group Claim value for administrator users. (Optional - requires claim name above)**: `admin`
    - **Group Claim value for restricted users. (Optional - requires claim name above)**: `restricted`
4. Click **Update Authentication Source**.

## Configuration verification

To confirm that authentik is properly configured with Forgejo, open Forgejo and sign in using the **Sign in with authentik** button.

## Resources

- [Forgejo documentation - Configuration Cheat Sheet: OAuth2 Client](https://forgejo.org/docs/latest/admin/config-cheat-sheet/#oauth2-client-oauth2_client)
- [Forgejo source - OpenID Connect provider](https://codeberg.org/forgejo/forgejo/src/branch/forgejo/services/auth/source/oauth2/providers_openid.go)
- [Forgejo source - OAuth2 callback handling](https://codeberg.org/forgejo/forgejo/src/branch/forgejo/routers/web/auth/oauth.go)
