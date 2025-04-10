---
title: Integrate with OpenProject
sidebar_label: OpenProject
support_level: community
---

## What is OpenProject

> OpenProject is a web-based project management software. Use OpenProject to manage your projects, tasks and goals. Collaborate via work packages and link them to your pull requests on Github.
>
> -- https://www.openproject.org/

## Preparation

The following placeholders are used in this guide:

- `openproject.company` is the FQDN of the OpenProject installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of OpenProject with authentik, you need to create a property mapping and an application/provider pair in authentik.

### Create a scope mapping

OpenProject requires a first and last name for each user. By default authentik only provides a full name, as a single string value. Therefore you need to create a property mapping to provide first and last names to OpenProject.

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.

- **Select type**: select **Scope Mapping** as the property mapping type.
- **Configure the Scope Mapping**: Provide a descriptive name (e.g. `Open Project Profile Scope`), and an optional description
    - **Scope name**: `profile`
    - **Expression**:

```python showLineNumbers
return {
    "name": request.user.name,
    "preferred_username": request.user.username,
    "nickname": request.user.username,
    "groups": [group.name for group in request.user.ak_groups.all()],
    "last_name": request.user.name.rsplit(" ", 1)[-1],
    "first_name": request.user.name.rsplit(" ", 1)[0],
}
```

3. Click **Finish** to save the property mapping.

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **OAuth2/OpenID Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - **Protocol settings**:
        - Note the **Client ID**,**Client Secret**, and **slug** values because they will be required later.
        - **Redirect URI**:
            - Strict: <kbd>https://<em>openproject.company</em>/auth/oidc-<em>authentik</em>/callback</kbd>
        - **Signing key**: select any available signing key.
    - **Advanced protocol settings**:
        - **Scopes**:
            - Remove `authentik default OAuth Mapping: OpenID 'profile'` from **Selected Scopes**.
            - Add the scope that you created in the previous section (e.g. `Open Project Profile Scope`) to **Selected Scopes**.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## OpenProject configuration

To support the integration of authentik with OpenProject, you need to configure authentication in the OpenProject administration interface.

1. Login to OpenProject as an admin, click on your profile icon at the top right and then **Administration**.
2. Navigate to **Authentication** > **OpenID providers**.
3. Provide a display name (e.g. `Authentik`) and click **Save**.
4. Click on **I have a discover endpoint URL** and enter:
    <kbd>https://<em>authentik.company</em>/application/o/<em>openproject</em>/.well-known/openid-configuration</kbd>
5. Under **Advanced configuration** > **Metadata** the values should be automatically populated based on your discovery endpoint URL. If not, these values can be copied from the **Overview** page of the OpenProject provider in authentik.
6. Under **Advanced configuration** > **Client details** enter your authentik client ID and client secret.
7. Under **Optional configuration** > **Attribute mapping** enter the following required configurations:
    - **Mapping for: Username**: `preferred_username`
    - **Mapping for: Email**: `email`
    - **Mapping for: First Name**: `first_name`
    - **Mapping for: Last Name**: `last_name`

## Configuration verification

To confirm that authentik is properly configured with OpenProject, log out, click on the **authentik** button and enter your authentik credentials.
