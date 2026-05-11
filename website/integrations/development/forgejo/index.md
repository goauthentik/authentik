---
title: Integrate with Forgejo
sidebar_label: Forgejo
support_level: community
---

## What is Forgejo?

> Forgejo is a lightweight, self‑hosted alternative to GitHub/GitLab, with a strong emphasis on community governance and open development.
>
> -- https://forgejo.org/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `forgejo.company` is the FQDN of the Forgejo installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Forgejo with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID**, **Client Secret**, and **slug** values because they will be required later.
        - Set a `Strict` redirect URI to `https://<forgejo.company>/user/oauth2/authentik/callback`.
        - Select any available signing key.
        - Under **Advanced protocol settings** > **Selected Scopes**, add `authentik default OAuth Mapping: OpenID 'entitlements'`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Forgejo configuration

1. Log in to Forgejo as an administrator, then click your profile icon in the top-right corner and select **Site Administration**.
2. Select the **Authentication Sources** tab and then click on **Add Authentication Source**.
3. Set the following required configurations:
    - **Authentication Name**: `authentik` (This must match the name used in the **Redirect URI** in the previous section)
    - **OAuth2 Provider**: `OpenID Connect`
    - **Client ID (Key)**: Enter the Client ID from authentik.
    - **Client Secret**: Enter the Client Secret from authentik.
    - **Icon URL**: `https://authentik.company/static/dist/assets/icons/icon.png`
    - **OpenID Connect Auto Discovery URL**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
    - **Additional Scopes**: `email profile`

4. Click **Add Authentication Source**.

### Configure permissions _(optional)_

Optionally, application entitlements and property mappings can be created to manage user permissions in Forgejo.

#### Create application entitlements

The following application entitlements will be created:

- `gituser`: normal Forgejo users.
- `gitadmin`: Forgejo users with administrative permissions.
- `gitrestricted`: restricted Forgejo users.

:::info Entitlement assignment is required
Users who are not assigned any of these entitlements will be denied login access. In contrast, users assigned the `gitadmin` entitlement will have full administrative privileges, while users assigned the `gitrestricted` entitlement will have limited access.
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

#### Add the custom property mapping to the Forgejo provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the **Edit** icon of the Forgejo provider.
3. Under **Advanced protocol settings** > **Scopes** add the following scopes to **Selected Scopes**:
    - `authentik default OAuth Mapping: OpenID 'email'`
    - `authentik default OAuth Mapping: OpenID 'profile'`
    - `authentik default OAuth Mapping: OpenID 'openid'`
    - `authentik forgejo OAuth Mapping: OpenID 'forgejo'`

4. Click **Update**.

#### Configure Forgejo to use the new claims

:::info
For this to function, the Forgejo `ENABLE_AUTO_REGISTRATION: true` variable must be set. More information on configuration variables is available in the [Forgejo Configuration Cheat Sheet](https://forgejo.org/docs/latest/admin/config-cheat-sheet/).
:::

1. Log in to Forgejo as an admin. Click your profile icon in the top-right corner, and then click **Site Administration**.
2. Select the **Authentication Sources** tab and edit the **authentik** Authentication Source.
3. Set the following configurations:
    - **Additional Scopes**: `email profile forgejo`
    - **Required Claim Name**: `forgejo`
    - **Claim name providing group names for this source.** (Optional): `forgejo`
    - **Group Claim value for administrator users.** (Optional - requires claim name to be set): `admin`
    - **Group Claim value for restricted users.** (Optional - requires claim name to be set): `restricted`
4. Click **Update Authentication Source**.

## Configuration verification

To verify that authentik is correctly set up with Forgejo, log out and then log back in using the **Sign in with authentik** button. You should be redirected to authentik, and once authenticated, you should then be signed in to Forgejo.

## Resources

- [Official Forgejo Documentation](https://forgejo.org/docs/latest/)
