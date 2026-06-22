---
title: Integrate with FortiGate Admin Login
sidebar_label: FortiGate Admin Login
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is FortiGate?

> FortiGate is Fortinet's next-generation firewall. FortiGate firewalls provide security services such as application control, intrusion prevention, web filtering, and VPN access.
>
> -- https://www.fortinet.com/products/next-generation-firewall

## Preparation

The following placeholders are used in this guide:

- `fortigate.company` is the FQDN of the FortiGate installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of FortiGate Admin Login with authentik, you need to create a SAML property mapping and an application/provider pair in authentik.

### Create a property mapping in authentik

FortiGate expects a SAML attribute named `username` that contains the FortiGate administrator username. This example uses the authentik username, but you can return any user attribute that matches the FortiGate administrator account name.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the type and click **Next**.
4. Create a property mapping with the following values:
    - **Name**: `FortiGate username`
    - **SAML Attribute Name**: `username`
    - **Expression**:

        ```python
        return request.user.username
        ```

5. Click **Finish** to save the property mapping.

### Create an application and provider in authentik

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because you will use it when configuring FortiGate.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://fortigate.company/saml/?acs`.
        - Set the **Audience** to `https://fortigate.company/metadata/`.
        - Set the **SLS URL** to `https://fortigate.company/saml/?sls`.
        - Under **Advanced protocol settings**:
            - Set the **Signing Certificate** to the certificate authentik should use to sign SAML responses.
            - Enable **Sign responses**.
            - Add `FortiGate username` to **Selected User Property Mappings**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the FortiGate Admin Login provider.
3. Click **Download** under **Download signing certificate**. You will import this certificate into FortiGate.

## FortiGate configuration

### Import the authentik signing certificate

1. Log in to the FortiGate administrative interface.
2. Navigate to **System** > **Certificates**.
3. Select **Create/Import** > **Remote Certificate**.
4. Upload the authentik signing certificate you downloaded earlier.
5. Note the certificate name that FortiGate assigns to the imported certificate.

### Configure SAML single sign-on

1. Navigate to **Security Fabric** > **Fabric Connectors**.
2. Open **Security Fabric Setup** and then open **Single Sign-On Settings**.
3. Enable **Service Provider (SP)** mode.
4. Configure the **SP settings**:
    - **SP Address**: `fortigate.company`
    - **Default login page**: select **Normal** while testing the integration. After SAML authentication is working, you can select **Single Sign-On** if FortiGate should redirect directly to authentik.
    - **Default admin profile**: select the administrator profile FortiGate should assign to SAML administrators created on first login. To require manual profile assignment before a new SAML administrator can access FortiGate, select `admin_no_access`.
5. Configure the **IdP Details**:
    - **IdP Type**: `Custom`
    - **IdP entity ID**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **IdP single sign-on URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **IdP single logout URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **IdP Certificate**: select the authentik signing certificate that you imported earlier.
6. Click **Apply** to save the configuration.

If your FortiGate web administration interface uses a non-standard HTTPS port, include the port in **SP Address** and in the authentik **ACS URL** and **SLS URL**.

### Confirm the SP details

FortiGate shows its **SP entity ID**, **SP ACS URL**, and **SP SLS URL** after you configure the **SP Address**. Confirm that these values match the **Audience**, **ACS URL**, and **SLS URL** values in the authentik provider. If FortiGate shows a different **SP entity ID**, update the authentik provider **Audience** value to match FortiGate exactly.

### Recovery and debugging

If SAML is set as the default login method and SAML authentication is not working, open `https://fortigate.company/saml/?acs` and select **Login Locally**, or use the FortiGate CLI to restore the normal login page:

```text
config system saml
    set default-login-page normal
end
```

To enable SAML debug logging, run the following commands and then repeat the login attempt:

```text
diagnose debug console timestamp enable
diagnose debug application httpsd -1
diagnose debug application samld -1
diagnose debug enable
```

When you are finished debugging, disable debug logging:

```text
diagnose debug disable
diagnose debug reset
```

## Configuration verification

To confirm that authentik is properly configured with FortiGate Admin Login, open FortiGate and sign in via authentik.

## Resources

- [Fortinet - Configuring SAML SSO](https://docs.fortinet.com/document/fortigate/8.0.0/administration-guide/254248/configuring-saml-sso)
- [Fortinet Community - Configuring SAML SSO login for FortiGate administrators with Entra ID acting as SAML IdP](https://community.fortinet.com/fortigate-3/technical-tip-configuring-saml-sso-login-for-fortigate-administrators-with-entra-id-acting-as-saml-idp-96661)
- [Fortinet Community - Configuring SAML SSO login for FortiGate administrators with Okta acting as SAML IdP](https://community.fortinet.com/fortigate-3/technical-tip-configuring-saml-sso-login-for-fortigate-administrators-with-okta-acting-as-saml-idp-97935)
