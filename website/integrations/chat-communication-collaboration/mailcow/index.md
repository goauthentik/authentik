---
title: Integrate with mailcow
sidebar_label: mailcow
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";

## What is mailcow?

> mailcow is a Dockerized, open-source groupware and email suite based on Docker. It relies on many well-known and long-used components, which, when combined, result in a comprehensive email server solution.
>
> -- https://mailcow.email/

## Preparation

The following placeholders are used in this guide:

- `mailcow.company` is the FQDN of the mailcow installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

<RedirectURI20265Note />

To support the integration of mailcow with authentik, you need to create property mappings, set user attributes, and create an application/provider pair in authentik.

### Create property mappings

mailcow requires users to have an email address. The custom email scope mapping returns the `email_verified` claim from a user attribute, and the `mailcow_template` scope mapping lets mailcow select a mailbox template when creating or updating mailboxes.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **New Property Mapping**.
3. Select **Scope Mapping** as the property mapping type. Use `email` as the scope name, and copy the user attribute expression from [Email scope verification](/docs/add-secure-apps/providers/oauth2/index.mdx#email-scope-verification).
4. Click **Create**.
5. Create another **Scope Mapping** using the following values:
    - **Name**: `mailcow_template`
    - **Scope name**: `mailcow_template`
    - **Expression**:

        ```python
        return {
            "mailcow_template": request.user.attributes.get("mailcow_template", "default"),
        }
        ```

6. Click **Create**.

### Set user attributes

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Users** and select a user that will use the mailcow integration.
3. Click **Edit User**.
4. Add the following attributes to the **Attributes** field:

    ```yaml
    email_verified: true
    mailcow_template: default
    ```

5. Click **Save Changes**.

Repeat these steps for all users that need to use the mailcow integration. The user's email address in authentik must match the mailcow mailbox address for existing mailboxes. If mailcow creates the mailbox during first login, the email domain must already exist in mailcow.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Note the **Client ID** and **Client Secret** values because they will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://mailcow.company`.
        - Select any available signing key.
        - Under **Advanced protocol settings**:
            - Remove the `authentik default OAuth Mapping: OpenID 'email'` scope from **Selected Scopes**.
            - Add the custom `email` scope mapping to **Selected Scopes**.
            - Add the `mailcow_template` scope mapping to **Selected Scopes**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## mailcow configuration

To configure mailcow with authentik, log in as an administrator and navigate to **System** > **Configuration**. Then, go to **Access** > **Identity Provider**, select `Generic-OIDC` as the identity provider, and enter the following information in the form:

- **Authorization endpoint**: `https://authentik.company/application/o/authorize/`
- **Token endpoint**: `https://authentik.company/application/o/token/`
- **User info endpoint**: `https://authentik.company/application/o/userinfo/`
- **Client ID**: `<Client ID from authentik>`
- **Client Secret**: `<Client Secret from authentik>`
- **Redirect URL**: `https://mailcow.company`
- **Attribute Mapping**:
    - **Attribute**: `default`
    - **Template**: Select the mailbox template that should be used for users with `mailcow_template: default`.

To let existing mailboxes log in with authentik, navigate to **E-Mail** > **Configuration** > **Mailboxes**, edit the mailbox, set **Identity Provider** to `Generic-OIDC`, and save the changes.

For users who do not already have mailboxes, mailcow can create a mailbox when the user signs in. Enable **Auto-create users on login** and configure either **Default Template** or an **Attribute Mapping** that matches the `mailcow_template` claim returned by authentik.

Users who log in with Generic-OIDC can create passwords for external mail clients from the mailcow UI by opening **Mailbox Settings** and using the **App Passwords** tab.

## Configuration verification

To confirm that authentik is properly configured with mailcow, open mailcow and log in via authentik.

## Resources

- [mailcow documentation - Generic-OIDC](https://docs.mailcow.email/manual-guides/mailcow-UI/u_e-mailcow_ui-generic-oidc/)
