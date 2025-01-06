---
title: Integrate with FortiGate Admin Login
sidebar_label: FortiGate Admin Login
---

# FortiGate Admin Login

<span class="badge badge--secondary">Support level: Community</span>

## What is FortiGate

> FortiGate is a firewall from FortiNet. It is a NGFW with layer7 inspection and able to become a part of a FortiNet security fabric.
> -- https://www.fortinet.com/products/next-generation-firewall
>
> This guide explains how to setup a FortiGate to use authentik as SAML provider for Admin Login. It does not cover how to setup SSLVPN logins, that is a different configuration.

## Preparation

The following placeholders are used in this guide:

- `fgt.company` is the FQDN of the FortiGate install.
- `authentik.company` is the FQDN of the authentik install.
- `fgt.mapping` is the name of the SAML Property Mapping.
- `ak.cert` = The authentik self-signed certificate you use for the service provider.

> [!IMPORTANT]
> If you have changed the port of the admin login from 443 to anything else you have to append it behind `fgt.company`. So f.e. `fgt.company:10443`.

## Custom Property Mapping

Create a new SAML Property Mapping under the Customization settings.

- `fgt.mapping` is the value for the Name.
- `username` is the value for the SAML Attribute Name.
- `return request.user.email` is the value for the Expression.

Create an application and SAML provider in authentik, and note the slug, because this will be used later. Create a SAML provider with the following parameters:

Provider:

- ACS URL: `https://fgt.company/saml/?acs`
- Issuer: `https://authentik.company`
- Service Provider Binding: Post
- Audience: `https://fgt.company/metadata/`
- Signing Certificate: `ak.cert`
- Property mappings: `fgt.mapping`

You can of course adjust durations.

Application:

- Name: `Fortigate`
- Slug: `fortigate`
- Launch URL: `https://fgt.company/`

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
