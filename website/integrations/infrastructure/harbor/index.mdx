---
title: Integrate with Harbor
sidebar_label: Harbor
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Harbor?

> Harbor is an open source container image registry that secures images with role-based access control, scans images for vulnerabilities, and signs images as trusted. A CNCF Graduated project, Harbor delivers compliance, performance, and interoperability to help you consistently and securely manage images across cloud native compute platforms like Kubernetes and Docker.
>
> -- https://goharbor.io

## Preparation

The following placeholders are used in this guide:

- `harbor.company` is the FQDN of the Harbor installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning Existing Harbor users
Harbor can switch from database authentication to OIDC only when no local users other than `admin` exist. If your Harbor instance already has local users, review Harbor's authentication-mode migration options before changing **Auth Mode**.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Harbor with authentik, you need to create an application/provider pair in authentik.

Harbor can read authentik group names from the default `profile` scope. If you want Harbor-specific group and administrator grants instead of global authentik group names, configure the optional Harbor entitlements scope below.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Set **Launch URL** to `https://harbor.company`. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://harbor.company/c/oidc/callback`.
        - Select any available signing key.
        - Under **Advanced protocol settings** > **Scopes**, add `authentik default OAuth Mapping: OpenID 'offline_access'` to **Selected Scopes**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Configure Harbor entitlements _(optional)_

Harbor uses the OIDC `groups` claim for group membership and system administrator assignment. To expose application entitlements as Harbor groups, create an OAuth2 scope mapping that sends Harbor-specific entitlement names in the `groups` claim.

1. In authentik, navigate to **Customization** > **Property Mappings** and click **New Property Mapping**.
2. Select **OAuth2 Scope Mapping** and use the following values:
    - **Name**: `Harbor entitlements`
    - **Scope name**: `harbor`
    - **Expression**:

        ```python
        return {
            "name": request.user.name,
            "preferred_username": request.user.username,
            "groups": [
                entitlement.name
                for entitlement in request.user.app_entitlements(provider.application)
            ],
        }
        ```

3. Open the Harbor provider that you created earlier and add `Harbor entitlements` to the selected **Scopes**.
4. Open the Harbor application and create the required **Application entitlements**. If you want to grant Harbor system administrator privileges through OIDC, create an entitlement such as `harbor-admin` and bind it to the users or groups that should receive that access.

## Harbor configuration

To support the integration of authentik with Harbor, you need to configure OIDC authentication.

1. Log in to the Harbor interface with a Harbor system administrator account.
2. Under **Administration**, navigate to **Configuration** and select the **Authentication** tab.
3. In the **Auth Mode** dropdown, select **OIDC** and provide the following values:
    - **OIDC Provider Name**: `authentik`
    - **OIDC Endpoint**: `https://authentik.company/application/o/<application_slug>/`
    - **OIDC Client ID**: enter the Client ID from authentik.
    - **OIDC Client Secret**: enter the Client Secret from authentik.
    - **Group Claim Name**: `groups`
    - **OIDC Admin Group** _(optional)_: enter the authentik group name or Harbor entitlement name that should receive Harbor system administrator privileges.
    - **OIDC Scope**: `openid,profile,email,offline_access`. If you configured the optional Harbor entitlements scope mapping, use `openid,email,harbor,offline_access`.
    - **Automatic onboarding**: enable this setting.
    - **Username Claim**: `preferred_username`
4. Click **Test OIDC Server** to validate the configuration.
5. Click **Save**.

After OIDC is enabled, Harbor shows **LOGIN VIA LOCAL DB** on the login page for the local Harbor administrator. You can also open `https://harbor.company/account/sign-in` directly to use local database authentication.

:::info Harbor external URL
If Harbor redirects users to an unexpected host, ensure that `hostname` or `external_url` is set correctly in `harbor.yml`. After updating `harbor.yml`, run Harbor's `prepare` script and restart Harbor.
:::

### Use Docker or Helm with OIDC accounts

Docker and Helm clients cannot complete browser-based OIDC redirects. After a user logs in to Harbor with authentik for the first time, they can use their Harbor CLI secret as the password for Docker or Helm.

1. Log in to Harbor with an OIDC user account.
2. Click the username at the top of the screen and select **User Profile**.
3. Click the clipboard icon to copy the CLI secret.
4. Use the CLI secret as the password when logging in from Docker or Helm.

## Configuration verification

To confirm that authentik is properly configured with Harbor, open Harbor and click **LOGIN WITH AUTHENTIK** on the login page. After a successful login, Harbor opens.

## Resources

- [Harbor documentation - Configure OIDC Provider Authentication](https://goharbor.io/docs/2.14.0/administration/configure-authentication/oidc-auth/)
- [Harbor documentation - Configure the Harbor YML File](https://goharbor.io/docs/2.14.0/install-config/configure-yml-file/)
- [Harbor documentation - Reconfigure Harbor and Manage the Harbor Lifecycle](https://goharbor.io/docs/2.14.0/install-config/reconfigure-manage-lifecycle/)
