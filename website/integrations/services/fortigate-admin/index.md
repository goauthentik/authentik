---
title: Integrate with FortiGate Admin Login
sidebar_label: FortiGate Admin Login
---

# Integrate with FortiGate Admin Login

<span class="badge badge--secondary">Support level: Community</span>

## What is FortiGate

> FortiGate is a firewall from FortiNet. It is a NGFW with layer7 inspection and able to become a part of a FortiNet security fabric.
>
> -- https://www.fortinet.com/products/next-generation-firewall

## Preparation

The following placeholders are used in this guide:

- `fortigate.company` is the FQDN of the FortiGate installation.
- `authentik.company` is the FQDN of the authentik installation.

- `fgt.mapping` is the name of the SAML Property Mapping.
- `ak.cert` = The authentik self-signed certificate you use for the service provider.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

> [!IMPORTANT]
> If you have changed the port of the admin login from 443 to anything else you have to append it behind `fortigate.company`. So f.e. `fortigate.company:10443`.

## Custom Property Mapping

Create a new SAML Property Mapping under the Customization settings.

- `fgt.mapping` is the value for the Name.
- `username` is the value for the SAML Attribute Name.
- `return request.user.email` is the value for the Expression.

Create an application and SAML provider in authentik, and note the slug, because this will be used later. Create a SAML provider with the following parameters:

Provider:

- ACS URL: `https://fortigate.company/saml/?acs`
- Issuer: `https://authentik.company`
- Service Provider Binding: Post
- Audience: `https://fortigate.company/metadata/`
- Signing Certificate: `ak.cert`
- Property mappings: `fgt.mapping`

You can of course adjust durations.

Application:

- Name: `Fortigate`
- Slug: `fortigate`
- Launch URL: `https://fortigate.company/`

## FortiGate Configuration

To integrate Fortigate with authentik, nagiate to <kbd>https://<em>fortigate.company</em>/ng/system/certificate</kbd> and import the certificate you configured in the previous section.

Once that is done, navigate to <kbd>https://<em>fortigate.company</em>/fabric-connector/edit/security-fabric-connection</kbd> and select **Single Sign-On** to configure SAML authentication. You should see, under **Mode**, a toggle named **Service Provider (SP)**, toggle it to enable this authentication method.

Then, set the following values in the Fortigate administrative UI:

- **SP Address**: <kbd><em>fortigate.company</em></kbd>
- **Default login page**: `Normal` or `Single Sign-On`, depending on your needs. `Normal` allows local and SAML authentication while the latter only allows SAML authentication.
- **Default admin profile**: Set this to an available profile.

Under **IdP Details**, set the following values:

- **SP entity ID**: `https`
- **IdP Type**: `Custom`
- **IdP entity ID**: <kbd>https://<em>authentik.company</em></kbd>
- **IdP Login URL**: <kbd>https://<em>authentik.company</em>/application/saml/<em>slug-from-authentik</em>/sso/binding/redirect/</kbd>
- **IdP Logout URL**: <kbd>https://<em>authentik.company</em>/application/saml/<em>slug-from-authentik</em>/slo/binding/redirect/</kbd>




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
Open this URL (`https://fortigate.company/saml/?acs`) in a browser and choose `Login Locally`.

**Method 2**:
Open the CLI and set the login page back to normal.

```bash
config system saml
    set default-login-page normal
end
```

## Ressources

- [Offocial Fortigate documentation on SAML authentication](https://community.fortinet.com/t5/FortiGate/Technical-Tip-Configuring-SAML-SSO-login-for-FortiGate/ta-p/194656)

## Configuration verification
