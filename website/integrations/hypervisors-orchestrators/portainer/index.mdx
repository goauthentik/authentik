---
title: Integrate with Portainer
sidebar_label: Portainer
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Portainer?

> Portainer is the operational control plane that lets enterprise IT teams run Kubernetes and Docker environments consistently, safely, predictably, and at scale.
>
> -- https://www.portainer.io/

## Preparation

The following placeholders are used in this guide:

- `portainer.company` is the FQDN of the Portainer installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Portainer with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it is required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they are required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` with the value `https://portainer.company/`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

## Portainer configuration

1. Log in to Portainer as a user with administrative privileges.
2. Navigate to **Settings** > **Authentication**.
3. Under **Authentication method**, select **OAuth**.
4. Configure the following settings:
    - **Use SSO**: enabled.
    - **Automatic user provisioning**: enabled.
5. Under **Provider**, select **Custom**.
6. Under **OAuth Configuration**, enter the following values:
    - **Client ID**: the **Client ID** from the authentik provider.
    - **Client Secret**: the **Client Secret** from the authentik provider.
    - **Authorization URL**: `https://authentik.company/application/o/authorize/`
    - **Access Token URL**: `https://authentik.company/application/o/token/`
    - **Resource URL**: `https://authentik.company/application/o/userinfo/`
    - **Redirect URL**: `https://portainer.company/`
    - **Logout URL**: `https://authentik.company/application/o/<application_slug>/end-session/`
    - **User Identifier**: `preferred_username`, or `email` if you prefer to use email addresses as identifiers.
    - **Scopes**: `openid profile email`
7. Click **Save settings**.

:::caution Scope separators
Do not use commas in the **Scopes** field. Use spaces only.
:::

### Configure automatic team membership _(optional)_

If you are using [Portainer Business Edition (BE)](https://www.portainer.io/take-3), it is possible to configure automatic team membership. This allows you to grant access to teams and environments, and automatically grant admin access to certain users based on authentik application entitlements. It is only possible to configure automatic group membership in Portainer BE. This cannot be configured in the Community Edition.

This section assumes that you already have two teams configured in Portainer: `engineering` and `sysadmins`. See [Portainer's documentation](https://docs.portainer.io/admin/user/teams) for information on managing teams and access to environments based on team membership.

This section also assumes that two application entitlements have been created in authentik: `Portainer Admins` and `Portainer Users`. You can choose any entitlement names and replace `Portainer Admins` and `Portainer Users` later in this guide with your chosen names.

#### Create application entitlements

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and open the Portainer application.
3. Click the **Application entitlements** tab.
4. Create two entitlements named `Portainer Admins` and `Portainer Users`.
5. Open each entitlement and bind the users or groups that should receive it.

#### Create a property mapping

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
    - **Select type**: select **Scope Mapping**.
    - **Configure the Scope Mapping**: Provide a descriptive name (e.g. `authentik portainer OpenID Mapping: OAuth 'groups'`), and an optional description.
        - **Scope name**: `groups`
        - **Expression**:

        ```python showLineNumbers
        entitlement_names = {
            entitlement.name
            for entitlement in request.user.app_entitlements(provider.application)
        }
        groups = []

        if "Portainer Admins" in entitlement_names:
            groups.append("admin")

        if "Portainer Users" in entitlement_names:
            groups.append("user")

        return {
            "groups": groups
        }
        ```

        This expression filters on the entitlement names `Portainer Admins` and `Portainer Users`. You can use any entitlements that exist on the Portainer application. Ensure that the names entered here exactly match those set up in authentik, as they are case-sensitive.

3. Click **Finish**.
4. Navigate to **Applications** > **Providers**.
5. Select your provider for Portainer and click **Edit**.
6. Under **Advanced protocol settings** > **Scopes**, add the property mapping created in the previous step to **Selected Scopes**.
7. Click **Update** to save your changes to the provider.

Since access to Portainer is based on application entitlements, configure a [binding](/docs/add-secure-apps/bindings-overview/) for the application in authentik so that access is restricted to the same users or groups that should be able to sign in to Portainer.

#### Update the Portainer settings

1. Log in to Portainer as a user with administrative privileges.
2. Navigate to **Settings** > **Authentication**.
3. Under **Team Membership**, toggle **Automatic team membership** to **ON**, and complete configuration as follows:
    - **Claim name**: `groups`
    - **Statically assigned teams**: Add two team mappings with the following values:
        - **claim value regex** `^user$` **maps to team** `engineering`.
        - **claim value regex** `^admin$` **maps to team** `sysadmins`.
    - **Default team**: `engineering`
    - **Admin mapping**:
        - Toggle **Assign admin rights to group(s)** to **ON**.
        - Add one admin mapping and set **claim value regex** to `^admin$`.
4. Under **Provider** > **OAuth Configuration**, append `groups` to **Scopes**. The full value for **Scopes** should then be `openid profile email groups`.
5. Click **Save settings**.

## Configuration verification

To verify the integration of authentik with Portainer, log out of Portainer, then on the login page click **Login with OAuth**. You should be redirected to authentik and, after successful authentication, automatically logged in to Portainer.

## Resources

- [Portainer Documentation - Authenticate via OAuth](https://docs.portainer.io/admin/settings/authentication/oauth)
- [Portainer Documentation - Add a new team](https://docs.portainer.io/admin/user/teams/add)
- [Portainer Documentation - Manage access to environments](https://docs.portainer.io/admin/environments/access)
