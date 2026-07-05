---
title: Integrate with Arcane
sidebar_label: Arcane
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Arcane?

> Arcane is a modern Docker management platform that provides a web interface for managing containers, images, volumes, networks, projects, and related Docker workflows.
>
> -- https://getarcane.app/

## Preparation

The following placeholders are used in this guide:

- `arcane.company` is the FQDN of the Arcane installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Arcane with authentik, you need to create an application/provider pair in authentik.

### Create custom scope mapping

Arcane blocks account merging when an existing local account has the same email address as the OIDC user and the OIDC provider returns `email_verified: false`. If you plan to enable account merging in Arcane, create a custom email scope mapping that returns `email_verified: true`.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
    - **Select type**: select **Scope Mapping**.
    - **Configure the Scope Mapping**: Provide a descriptive name (e.g. `Arcane Email Scope`), and an optional description.
        - **Scope name**: `email`
        - **Expression**:

        ```python showLineNumbers
        return {
            "email": request.user.email,
            "email_verified": True
        }
        ```

3. Click **Finish** to save the property mapping.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://arcane.company/auth/oidc/callback`.
        - Select any available signing key.
        - Under **Advanced protocol settings**:
            - If you created the custom scope mapping, remove the `authentik default OAuth Mapping: OpenID 'email'` scope, and add the custom scope mapping.
            - If you plan to configure Arcane role mappings, add the `authentik default OAuth Mapping: Application Entitlements` scope mapping.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Create application entitlements _(optional)_

If you want Arcane to assign roles from authentik, create one application entitlement for each Arcane role mapping that you plan to configure.

1. In the authentik Admin interface, navigate to **Applications** > **Applications** and click the Arcane application.
2. Click the **Application entitlements** tab, and then click **Create entitlement**.
3. Enter a name for the entitlement, such as `arcane-admins`, and click **Create**.
4. Expand the entitlement details, click **Bind existing group/user**, and bind the entitlement to the users or groups that should receive the matching Arcane role.

## Arcane configuration

Arcane can be configured from the web interface or with environment variables. Use the web interface unless you manage Arcane configuration through deployment files.

### Configure OIDC in the web interface

1. Log in to Arcane as an administrator.
2. Navigate to **Settings** > **Security** > **OIDC Authentication**.
3. Configure the following values:
    - **Enable OIDC Authentication**: enable this option.
    - **OIDC Client ID**: enter the **Client ID** from authentik.
    - **OIDC Client Secret**: enter the **Client Secret** from authentik.
    - **OIDC Issuer URL**: `https://authentik.company/application/o/<application_slug>`
    - **Provider Display Name**: `authentik`
    - **OIDC Account Merging**: enable this option if you want OIDC logins to link to existing Arcane accounts by matching email address. If you enable this option, use the custom email scope mapping in the authentik provider.
4. Copy the **Redirect URI** shown by Arcane and verify that it matches `https://arcane.company/auth/oidc/callback`.
5. Save and test the connection.

### Configure environment variables _(optional)_

Add the following environment variables to your Arcane `.env` file:

```env title=".env"
APP_URL=https://arcane.company
OIDC_ENABLED=true
OIDC_CLIENT_ID=<Client ID from authentik>
OIDC_CLIENT_SECRET=<Client Secret from authentik>
OIDC_ISSUER_URL=https://authentik.company/application/o/<application_slug>
OIDC_PROVIDER_NAME=authentik
OIDC_SCOPES="openid email profile"
```

If you want OIDC logins to link to existing Arcane accounts by matching email address, also add the following setting and use the custom email scope mapping in the authentik provider:

```env title=".env"
OIDC_MERGE_ACCOUNTS=true
```

Restart Arcane to apply the changes.

### Configure role mappings _(optional)_

Arcane can map OIDC claim values to Arcane roles. This guide uses authentik application entitlements as the source of those claim values.

If you configured Arcane in the web interface:

1. In Arcane, navigate to **Settings** > **Security** > **OIDC Authentication**.
2. Set **Scopes** to `openid email profile entitlements`.
3. Set **OIDC Groups Claim** to `roles`.
4. Under **OIDC Mappings**, click **Create OIDC mapping**.
5. Set **Claim value** to the authentik application entitlement name, select the Arcane **Role**, select the **Environment scope**, and save the mapping.

If you configured Arcane with environment variables, update your `.env` file:

```env title=".env"
OIDC_SCOPES="openid email profile entitlements"
OIDC_GROUPS_CLAIM=roles
OIDC_ROLE_MAPPINGS='[{"claimValue":"arcane-admins","roleId":"role_admin"}]'
```

Restart Arcane to apply the changes.

## Configuration verification

To confirm that authentik is properly configured with Arcane, open Arcane and select **Sign in with authentik**.

## Resources

- [Arcane Docs - OIDC Single Sign-On](https://getarcane.app/docs/configuration/sso)
