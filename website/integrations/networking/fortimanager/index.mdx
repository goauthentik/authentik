---
title: Integrate with FortiManager
sidebar_label: FortiManager
support_level: community
---

## What is FortiManager?

> FortiManager is an enterprise solution that enables centralized network management, ensures compliance with best practices, and automates workflows to enhance breach protection.
>
> -- https://www.fortinet.com/products/management/fortimanager

## Preparation

The following placeholders are used in this guide:

- `fortimanager.company` is the FQDN of the FortiManager installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of FortiManager with authentik, you need to create a SAML property mapping and an application/provider pair in authentik.

### Create a property mapping in authentik

FortiManager expects a SAML attribute named `username` that contains the value used to identify the administrator account. This example uses the authentik username, but you can return any user attribute that matches the FortiManager administrator identifier.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the type and click **Next**.
4. Create a property mapping with the following values:
    - **Name**: `FortiManager username`
    - **SAML Attribute Name**: `username`
    - **Expression**:

        ```python
        return request.user.username
        ```

5. Click **Finish** to save the property mapping.

:::info Optional SAML attributes
FortiManager also accepts `profilename` and `adoms` attributes. The `profilename` attribute assigns a matching admin profile that already exists on FortiManager. The `adoms` attribute grants access to one or more administrative domains (ADOMs). To use either attribute, create additional SAML provider property mappings with the corresponding **SAML Attribute Name**, return the desired values from the **Expression**, and add the mappings to **Selected User Property Mappings** when configuring the provider.
:::

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because you will use it when configuring FortiManager.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://fortimanager.company/saml/?acs`.
        - Set the **SLS URL** to `https://fortimanager.company/saml/?sls`.
        - Under **Advanced protocol settings**:
            - Set the **Signing Certificate** to any available certificate.
            - Add `FortiManager username` to **Selected User Property Mappings**.
            - Set the **NameID Property Mapping** to `authentik default SAML Mapping: Username`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## FortiManager configuration

1. Log in to the FortiManager web interface as an administrator.
2. Navigate to **System Settings** > **SAML SSO**.
3. Configure the **Single Sign-On Settings**:
    - **Server Address**: `fortimanager.company`
    - **Single Sign-On Mode**: `Service Provider (SP)`
    - **SP Certificate**: select an available certificate.
    - **Default Login Page**: select whether FortiManager should show the normal login page with an SSO option, or redirect directly to authentik.
    - **Auto Create Admin**: enable this setting if FortiManager should create SSO administrators on first login. If you leave it disabled, create matching SSO administrators in FortiManager before testing the integration.
4. Configure the **IdP Settings**:
    - **IdP Type**: `Custom`
    - **IdP Entity ID**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **IdP Login URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **IdP Logout URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **IdP Certificate**: import the signing certificate that you selected in the authentik SAML provider. You can download it from the authentik SAML provider page, under **Related objects** > **Download signing certificate**.
5. If you enabled any options under **Signing Options** in FortiManager, align them with the corresponding options under **Advanced protocol settings** in the authentik SAML provider.
6. Click **Apply** to save the configuration.

:::info Administrator permissions
With **Auto Create Admin** enabled, newly-created SSO administrators receive the configured default admin profile. If users should receive permissions through SAML attributes instead, create matching FortiManager admin profiles and administrative domains, and send the optional `profilename` and `adoms` attributes from authentik.
:::

## Configuration verification

To confirm that authentik is properly configured with FortiManager, open FortiManager and sign in via authentik.

## Resources

- [FortiManager Administration Guide - SAML admin authentication](https://docs.fortinet.com/document/fortimanager/8.0.0/administration-guide/981386/saml-admin-authentication)
- [FortiManager CLI Reference - SAML](https://docs.fortinet.com/document/fortimanager/8.0.0/cli-reference/91498/saml)
