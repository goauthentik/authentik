---
title: Integrate with Xen Orchestra
sidebar_label: Xen Orchestra
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is Xen Orchestra?

> Xen Orchestra provides a user-friendly web interface for every Xen-based hypervisor, including XenServer and XCP-ng.
>
> -- https://xen-orchestra.com/

## Preparation

Xen Orchestra supports authentication plugins for OpenID Connect (OIDC), SAML, and LDAP. This guide uses the `auth-oidc` plugin. Xen Orchestra Appliance (XOA) includes this plugin. If you run Xen Orchestra from source, ensure that the `xo-server-auth-oidc` package is installed.

The following placeholders are used in this guide:

- `xenorchestra.company` is the FQDN of the Xen Orchestra installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of Xen Orchestra with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it is required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://xenorchestra.company/signin/oidc/callback`.
        - Select any available signing key.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Configure group claims _(optional)_

Xen Orchestra can synchronize OIDC `groups` claim values to Xen Orchestra groups. Use application entitlements to keep these group values scoped to this Xen Orchestra application.

1. Open the Xen Orchestra application that you created in authentik.
2. Click the **Application entitlements** tab.
3. Create one entitlement for each Xen Orchestra group value that authentik should send.
4. Bind the appropriate users or groups to each entitlement.
5. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **Scope Mapping** with the following settings:
    - **Name**: choose a descriptive name, such as `authentik Xen Orchestra OAuth Mapping: OpenID 'profile'`.
    - **Scope name**: `profile`
    - **Expression**:

        ```python showLineNumbers
        return {
            "name": request.user.name,
            "given_name": request.user.name,
            "preferred_username": request.user.username,
            "nickname": request.user.username,
            "groups": sorted(
                entitlement.name
                for entitlement in request.user.app_entitlements(provider.application)
            ),
        }
        ```

6. Click **Finish**.
7. Navigate to **Applications** > **Providers** and edit the Xen Orchestra provider.
8. Under **Advanced protocol settings** > **Selected Scopes**, remove `authentik default OAuth Mapping: OpenID 'profile'` and add the scope mapping that you just created.
9. Click **Update**.

## Xen Orchestra configuration

1. Log in to Xen Orchestra as an administrator.
2. Navigate to **Settings** > **Plugins**.
3. Find the `auth-oidc` plugin and click **+** next to the plugin name to expand the configuration options.
4. Configure the following settings:
    - **Auto-discovery URL**: `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
    - **Client identifier (key)**: enter the Client ID from authentik.
    - **Client secret**: enter the Client Secret from authentik.
    - **Fill information (optional)**: select this option to show the advanced fields.
    - **Scopes**: `profile email`
5. Click **Save configuration**.
6. Toggle the switch next to the `auth-oidc` plugin name to enable it.

If you want Xen Orchestra to identify users by their email addresses instead of their authentik usernames, set **Username field** to `email`.

:::info Xen Orchestra permissions
The first time a user signs in with OpenID Connect, Xen Orchestra creates a user without permissions. Assign the required ACLs to the user or to synchronized OIDC groups in Xen Orchestra.
:::

## Configuration verification

To confirm that authentik is properly configured with Xen Orchestra, log out of Xen Orchestra and click **Sign in with OpenID Connect** on the login page. You should be redirected to authentik and returned to Xen Orchestra after authentication.

## Resources

- [Xen Orchestra Documentation - Users](https://docs.xen-orchestra.com/xo5/users#openid-connect)
- [Xen Orchestra GitHub - auth-oidc plugin](https://github.com/vatesfr/xen-orchestra/tree/master/packages/xo-server-auth-oidc)
