---
title: Integrate with OpenProject
sidebar_label: OpenProject
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is OpenProject?

> OpenProject is a web-based project management software. Use OpenProject to manage your projects, tasks and goals. Collaborate via work packages and link them to your pull requests on GitHub.
>
> -- https://www.openproject.org/

## Preparation

The following placeholders are used in this guide:

- `openproject.company` is the FQDN of the OpenProject installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info OpenProject Enterprise add-on
OpenID Connect providers is an OpenProject Enterprise add-on. If **OpenID providers** is not available in your OpenProject instance, activate the Enterprise edition before continuing.
:::

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of OpenProject with authentik, you need to create a property mapping and an application/provider pair in authentik.

### Create a scope mapping

OpenProject requires a first and last name for each user. By default, authentik only stores a user's full name as a single string. Therefore you need to create a property mapping to provide separate first and last names to OpenProject.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
    - **Select type**: select **Scope Mapping** as the property mapping type.
    - **Configure the Scope Mapping**: provide a descriptive name (e.g. `OpenProject Profile Scope`), and an optional description.
        - **Scope name**: `profile`
        - **Expression**:

        ```python showLineNumbers
        name = request.user.name or request.user.username
        first_name, _, last_name = name.rpartition(" ")

        return {
            "name": name,
            "given_name": first_name or name,
            "family_name": last_name or name,
            "preferred_username": request.user.username,
            "nickname": request.user.username,
            "groups": [group.name for group in request.user.groups.all()],
            "first_name": first_name or name,
            "last_name": last_name or name,
        }
        ```

3. Click **Finish** to save the property mapping.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - **Protocol settings**:
            - Note the **Client ID** and **Client Secret** values because they will be required later.
            - **Redirect URI**:
                - `Strict` `Authorization`: `https://openproject.company/auth/oidc-authentik/callback`
            - **Signing Key**: select any available signing key.
        - **Advanced protocol settings**:
            - **Scopes**:
                - Remove `authentik default OAuth Mapping: OpenID 'profile'` from **Selected Scopes**.
                - Add the scope that you created in the previous section (e.g. `OpenProject Profile Scope`) to **Selected Scopes**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## OpenProject configuration

To support the integration of authentik with OpenProject, you need to configure authentication in the OpenProject administration interface.

1. Log in to OpenProject as an administrator, click your profile icon in the top-right corner, and then click **Administration**.
2. Navigate to **Authentication** > **OpenID providers**.
3. Click **+ OpenID provider** and select **Custom**.
4. Set **Display Name** to `authentik` to match the `/auth/oidc-authentik/callback` redirect URI configured in authentik.
5. In the discovery endpoint section, select **I have a discovery endpoint URL**, and enter:
   `https://authentik.company/application/o/<application_slug>/.well-known/openid-configuration`
6. Continue to **Advanced configuration** > **Metadata**. The values should be automatically populated based on your discovery endpoint URL. If not, copy these values from the **Overview** page of the OpenProject provider in authentik.
7. Under **Advanced configuration** > **Client details**, enter the **Client ID** and **Client Secret** values from authentik.
8. Under **Optional configuration** > **Attribute mapping**, enter the following required configurations:
    - **Mapping for: Username**: `preferred_username`
    - **Mapping for: Email**: `email`
    - **Mapping for: First Name**: `first_name`
    - **Mapping for: Last Name**: `last_name`
9. Click **Finish setup**.

OpenProject can optionally synchronize groups from the `groups` claim included in the scope mapping above. Enable **Synchronize groups** only if authentik should become responsible for OpenProject group assignments for users who log in with this provider. When enabled, OpenProject removes group memberships that are not included in the claim on each login.

## Configuration verification

To confirm that authentik is properly configured with OpenProject, log out of OpenProject, and then click on **authentik** and enter your authentik credentials to log back in.

## Resources

- [OpenProject Documentation - OpenID providers](https://www.openproject.org/docs/system-admin-guide/authentication/openid-providers/)
