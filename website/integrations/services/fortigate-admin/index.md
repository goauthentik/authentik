---
title: Integrate with FortiGate Admin Login
sidebar_label: FortiGate Admin Login
support_level: community
---

## What is FortiGate

> FortiGate is a firewall from FortiNet. It is a NGFW with layer7 inspection and able to become a part of a FortiNet security fabric.
> -- https://www.fortinet.com/products/next-generation-firewall
>
> This guide explains how to setup a FortiGate to use authentik as SAML provider for Admin Login. It does not cover how to setup SSLVPN logins, that is a different configuration.

## Preparation

The following placeholders are used in this guide:

- `fgt.company` is the FQDN of the FortiGate installation.
- `authentik.company` is the FQDN of the authentik installation.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of FortiGate with authentik, you need to create an application/provider pair in authentik.

### Create property mapping

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create a **SAML Provider Property Mapping** with the following settings:

- **Name**: Choose a descriptive name
- **SAML Attribute Name**: <kbd>username</kbd>
- **Friendly Name**: Leave blank
- **Expression**: <kbd>return request.user.email</kbd>

### Create an application and provider in authentik

1. Log in to authentik as an admin, and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to <kbd>https://<em>fgt.company</em>/saml/?acs</kbd>.
    - Set the **Issuer** to <kbd>https://<em>authentik.company</em></kbd>.
    - Set the **Audience** to <kbd>https://<em>fgt.company</em>/metadata</kbd>.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, add the **Property Mapping** you created in the previous section, then select an available **Signing Certificate**.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## FortiGate Configuration

Navigate to `https://fgt.company/ng/system/certificate` and Import the Certificate `ak.cert` to the FortiGate.
Then navigate to `https://fgt.company/fabric-connector/edit/security-fabric-connection` and select `Single Sign-On Settings` to configure SAML.

- Select `Service Provider (SP)` under Mode to enable SAML authentication.
- Set the `SP Address` to the FortiGate FQDN `fgt.company`. (This gives you the URLs to configure in authentik)
- Set the `Default Login Page` to either `Normal` or `Single-Sign On`. (Normal allows both local and SAML authentication vs only SAML SSO.)

FortiGate creates a new user by default if one does not exist, so you will need to set the Default Admin Profile to the permissions you want any new users to have. (I have created a `no_permissions` profile to assign by default.)

Under `SP Details` set the **SP entity ID** to `https`. Note it for later use (this is your Audience value of the authentik SP-provider).

> [!IMPORTANT]
> On both `IdP Login and Logout URL` change the `<SLUG>` to your own from the authentik application you have created.

- Set `IdP Type` to `Custom`
- Set `IdP entity ID` to `https://authentik.company`
- Set `IdP Login URL` to `https://authentik.company/application/saml/<SLUG>/sso/binding/redirect/`
- Set `IdP Logout URL` to `https://authentik.company/application/saml/<SLUG>/slo/binding/redirect/`
- Set `IdP Certificate` to `ak.cert`

## Troubleshooting

These are just suggestions of what **could** be the cause of an issue and how to enable debug on the FortiGate.

**Enabling debug on the FortiGate**
You can use the following commands on the FortiGate to enable debugging:

1. Debug saml daemon
   This will provide all possible output from the SAML daemon.
   `diag debug application samld -1`

2. Enable debug timestamps (optional)
   `diagnose debug console timestamp enable`

3. Enabling debug output
   Before you can see any output you need to enable the debug mode.
   `diagnose debug enable`

4. If you used SSO Login only instead of Normal and you are not able to log in again, you can try one of the following methods:

**Method 1**:
Open this URL (`https://fgt.company/saml/?acs`) in a browser and choose `Login Locally`.

**Method 2**:
Open the CLI and set the login page back to normal.

```bash
config system saml
    set default-login-page normal
end
```
