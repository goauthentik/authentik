---
title: Integrate with Box
sidebar_label: Box
support_level: community
---

## What is Box?

> Box is a cloud content management platform for secure file storage, sharing, collaboration, e-signatures, and content workflows.
>
> -- https://www.box.com/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::info Box requirements
Box SSO requires a Business or Enterprise account. To let Box create users automatically from SSO, make sure each authentik user has an email address and a full name with a first and last name.
:::

## authentik configuration

To support the integration of Box with authentik, you need to create property mappings and an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Create three **SAML Provider Property Mapping**s with the following settings:
    - **Email mapping**:
        - **Name**: `Box email`
        - **SAML Attribute Name**: `email`
        - **Expression**:

            ```python
            return request.user.email
            ```

    - **First name mapping**:
        - **Name**: `Box firstName`
        - **SAML Attribute Name**: `firstName`
        - **Expression**:

            ```python
            name = request.user.name.strip()
            return name.split(" ", 1)[0] if name else ""
            ```

    - **Last name mapping**:
        - **Name**: `Box lastName`
        - **SAML Attribute Name**: `lastName`
        - **Expression**:

            ```python
            name = request.user.name.strip()
            return name.rsplit(" ", 1)[1] if " " in name else ""
            ```

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** as it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **ACS URL** to `https://sso.services.box.net/sp/ACS.saml2`.
        - Set **Audience** to `box.net`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
            - Add the three property mappings that you created in the previous section.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Download metadata file

1. In authentik, navigate to **Applications** > **Providers** and click the provider that you created for Box.
2. Under **Related objects** > **Metadata**, click **Download**. This metadata file is required in the next section.

## Box configuration

1. Log in to Box and open the **Admin Console**.
2. Navigate to **Enterprise Settings** > **User Settings**.
3. In the **Configure Single Sign-On (SSO) for All Users** section, click **Configure**.
4. Submit the [Box SSO Setup Support Form](https://support.box.com/hc/en-us/requests/new) and provide the authentik metadata file.
5. Use the following values for individual SAML fields:
    - **Entity ID**, **Connection ID**, or **External Key**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **Redirect URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **Public Certificate**: the signing certificate from the authentik SAML provider.
    - **Email attribute**: `email`
    - **First name attribute**: `firstName`
    - **Last name attribute**: `lastName`
6. After Box processes the SSO configuration, return to **Admin Console** > **Enterprise Settings** > **User Settings**.
7. In the **Enable Single Sign-On (SSO) for All Users** section, enable **SSO Test Mode**.
8. After you test the integration, disable **SSO Test Mode** and enable **SSO Required**.

:::warning SSO Required
Test the SSO login flow before enabling **SSO Required**. Enabling **SSO Required** limits managed users to SSO login and is treated by Box as a critical administrator action.
:::

## Box SSO account settings

### On-the-fly registration _(optional)_

Box can create user accounts when a user signs in with SSO for the first time. To use on-the-fly registration, contact Box Customer Success or Box Product Support and provide the `email`, `firstName`, and `lastName` SAML attribute names.

### Group membership _(optional)_

Box can update Box group membership from SAML assertions when users sign in. To send authentik group names to Box, add `authentik default SAML Mapping: Groups` to the Box SAML provider's **Property mappings**.

If Box does not show the **User Groups Settings** section after SSO is enabled, contact Box Customer Success or Box Product Support to enable SAML groups. Nested group membership is not supported by Box.

## Configuration verification

To confirm that authentik is properly configured with Box, open Box in a private or incognito browser window. Click **Sign In with SSO**, enter the email address of a managed Box user, and confirm that you are redirected to authentik and then back to Box.

## Resources

- [Box Support - Setting Up Single Sign-On (SSO) for Your Organization](https://support.box.com/hc/en-us/articles/360043696514-Setting-Up-Single-Sign-On-SSO-for-Your-Organization)
- [Box Support - Logging in with Single Sign On (SSO)](https://support.box.com/hc/en-us/articles/360044195153-Logging-in-with-Single-Sign-On-SSO)
