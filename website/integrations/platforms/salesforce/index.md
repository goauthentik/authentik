---
title: Integrate with Salesforce
sidebar_label: Salesforce
support_level: community
---

## What is Salesforce

> Salesforce is a cloud-based CRM platform that provides sales, service, marketing, and analytics applications. To learn more, visit https://salesforce.com.

## Preparation

The following placeholders are used in this guide:

- `company.my.salesforce.com` is the FQDN of your Salesforce organization.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

For additional information about integrating with Salesforce, refer to their [SAML SSO documentation](https://help.salesforce.com/s/articleView?id=sf.sso_saml.htm&type=5) and [JIT provisioning documentation](https://help.salesforce.com/s/articleView?id=sf.sso_jit_requirements.htm&type=5).

## authentik configuration

To support the integration of Salesforce with authentik, you need to create property mappings for Just-in-Time (JIT) user provisioning and an application/provider pair.

### Create property mappings

Salesforce JIT provisioning requires specific SAML attributes to automatically create users on first login.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create five **SAML Provider Property Mapping**s with the following settings:
    - **Username Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `User.Username`
        - **Expression**:
            ```python
            return request.user.email
            ```
    - **Email Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `User.Email`
        - **Expression**:
            ```python
            return request.user.email
            ```
    - **Last Name Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `User.LastName`
        - **Expression**:
            ```python
            return request.user.name.split()[-1] if request.user.name else "User"
            ```
    - **Profile ID Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `User.ProfileId`
        - **Expression** (replace with your Salesforce Profile ID):
            ```python
            return "00eXXXXXXXXXXXXX"
            ```
    - **Federation Identifier Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `User.FederationIdentifier`
        - **Expression**:
            ```python
            return request.user.email
            ```

:::note
To find your Salesforce Profile ID, navigate to **Setup** > **Users** > **Profiles** in Salesforce, click on the desired profile, and copy the 18-character ID from the URL (starts with `00e`).
:::

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair.

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to `https://company.my.salesforce.com?so=XXXXXXXXX`, replacing `XXXXXXXXX` with your Salesforce Organization ID.
    - Set the **Issuer** to a unique identifier (e.g., `https://authentik.company`).
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**:
        - Select an available **Signing Certificate**.
        - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
        - Add all five **Property Mappings** you created in the previous section.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate

1. Navigate to **Applications** > **Providers** and click on the name of the SAML provider you created.
2. Under **Related objects** > **Download signing certificate**, click **Download**. This certificate will be required for the Salesforce configuration.

## Salesforce configuration

### Enable SAML Single Sign-On

1. Log in to Salesforce as an administrator.
2. Navigate to **Setup** > **Identity** > **Single Sign-On Settings**.
3. Click **Edit** and enable **SAML Enabled**.
4. Click **Save**.

### Create a new SAML Single Sign-On configuration

1. In the **Single Sign-On Settings** page, under **SAML Single Sign-On Settings**, click **New**.
2. Enter the following values:
    - **Name**: `authentik`
    - **Issuer**: Enter the same issuer value you configured in authentik (e.g., `https://authentik.company`).
    - **Identity Provider Certificate**: Upload the signing certificate you downloaded from authentik.
    - **Request Signing Certificate**: Select the default certificate or leave as-is.
    - **Request Signature Method**: `RSA-SHA256`
    - **SAML Identity Type**: Select **Assertion contains the Federation ID from the User object**.
    - **SAML Identity Location**: Select **Identity is in the NameIdentifier element of the Subject statement**.
    - **Service Provider Initiated Request Binding**: `HTTP POST`
    - **Identity Provider Login URL**: Enter the **SSO URL (Post)** from your authentik provider.`https://authentik.company/application/saml/<slug>/sso/binding/post/`
3. Click **Save**.

### Enable Just-in-Time provisioning

1. On the SAML Single Sign-On configuration page you just created, click **Edit**.
2. Under **Just-in-Time User Provisioning**, check **User Provisioning Enabled**.
3. Select **Standard** for the provisioning type.
4. Click **Save**.

## References

- [Salesforce SAML SSO Documentation](https://help.salesforce.com/s/articleView?id=sf.sso_saml.htm&type=5)
- [Salesforce JIT Provisioning Requirements](https://help.salesforce.com/s/articleView?id=sf.sso_jit_requirements.htm&type=5)
