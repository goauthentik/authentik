---
title: Integrate with FortiAnalyzer
sidebar_label: FortiAnalyzer
support_level: community
---

## What is FortiAnalyzer?

> FortiAnalyzer is a centralized log management, analytics, and reporting platform for Fortinet devices and the Fortinet Security Fabric.
>
> -- https://www.fortinet.com/products/management/fortianalyzer

This guide was tested with FortiAnalyzer 8.0.

## Preparation

The following placeholders are used in this guide:

- `faz.company` is the FQDN of the FortiAnalyzer installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of FortiAnalyzer with authentik, you need to create a SAML property mapping and an application/provider pair in authentik.

### Create a property mapping in authentik

FortiAnalyzer expects a SAML attribute named `username` that contains the value used to identify the administrator account. Create a custom SAML property mapping that exposes this value. This example uses the authentik username, but you can return any user attribute (for example, the email address) that you prefer to use as the FortiAnalyzer identifier.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the type and click **Next**.
4. Create a property mapping with the following values:
    - **Name**: `FortiAnalyzer username`
    - **SAML Attribute Name**: `username`
    - **Expression**:

        ```python
        return request.user.username
        ```

5. Click **Finish** to save the property mapping.

:::info
FortiAnalyzer also accepts two optional SAML attributes: `profilename` (assigns a matching admin profile that already exists on FortiAnalyzer, overriding the **Default Admin Profile**) and `adoms` (grants the user access to one or more ADOMs). To use them, create additional SAML provider property mappings with the corresponding **SAML Attribute Name**, return the desired values from the **Expression**, and add the new mappings to **Selected User Property Mappings** when configuring the provider.
:::

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. (Alternatively, you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application Name**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because you will use it when configuring FortiAnalyzer.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://faz.company/saml/?acs`.
        - Set the **SLS URL** to `https://faz.company/saml/?sls`.
        - Set the **SLS Binding** to `Post`.
        - Set the **Logout Method** to `Back-channel (POST)`.
        - Under **Advanced protocol settings**:
            - Set the **Signing Certificate** to any available certificate.
            - Optionally, enable **Sign assertions**, **Sign responses**, **Sign logout requests**, and **Sign logout response** for stronger security. The corresponding options under **Signing Options** in FortiAnalyzer must be aligned with this choice.
            - Add `FortiAnalyzer username` to **Selected User Property Mappings**.
            - Set the **NameID Property Mapping** to `authentik default SAML Mapping: Username`.
            - Set the **Issuer** to `https://authentik.company`.
            - Set the **Service Provider Binding** to `Post`.
            - Ensure that the **Digest algorithm** and **Signature algorithm** are set to at least `SHA256`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## FortiAnalyzer configuration

1. Log in to the FortiAnalyzer web interface as an administrator.
2. Navigate to **System Settings** > **SAML SSO**.
3. Configure the **Single Sign-On Settings**:
    - **Server Address**: `faz.company`
    - **Single Sign-On Mode**: `Service Provider (SP)`
    - **SP Certificate**: select an available certificate (for example, the default `Fortinet_Local`).
    - **Signature Algorithm**: select at least `RSA-SHA256`.
    - **Digest Method**: select at least `SHA256`.
    - **Default Login Page**: `Single-Sign On`
    - **Auto Create Admin**: enabled
    - **Default Admin Profile**: `No_Permission_User`
4. Optionally, under **Signing Options**, enable the following for stronger security. The corresponding sign options in the authentik provider must be aligned with this choice:
    - **Authentication Request Signed**
    - **Logout Request Signed**
    - **Require Assertions Signed from IdP**
    - **Require Logout Response Signed**
5. Configure the **IdP Settings**:
    - **IdP Type**: `Custom`
    - **IdP Entity ID**: `https://authentik.company`
    - **IdP Login URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/redirect/`
    - **IdP Logout URL**: `https://authentik.company/application/saml/<application_slug>/slo/binding/redirect/`
    - **IdP Certificate**: click **Import** and upload the public key of the signing certificate that you selected in the authentik SAML provider. You can download it from **System** > **Certificates** in the authentik Admin interface.
6. Click **Apply** to save the configuration.

:::info
With **Auto Create Admin** enabled and **Default Admin Profile** set to `No_Permission_User`, new SSO users are created without permissions. An administrator must edit each new user under **System Settings** > **Administrators** and assign an admin profile and ADOM access before the user can perform any actions.
:::

## Configuration verification

To confirm that authentik is properly configured with FortiAnalyzer, log out and log back in via authentik.

## Resources

- [FortiAnalyzer Administration Guide - SAML admin authentication](https://docs.fortinet.com/document/fortianalyzer/8.0.0/administration-guide/981386/saml-admin-authentication)
