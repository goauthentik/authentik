---
title: Integrate with FortiGate SSLVPN
sidebar_label: FortiGate SSLVPN
support_level: community
---

## What is FortiGate SSLVPN

> FortiGate is a firewall from FortiNet. It is a NGFW with layer7 inspection and able to become a part of a FortiNet security fabric.
>
> -- https://www.fortinet.com/products/next-generation-firewall

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of your authentik installation
- `fortigate.company` is the FQDN of your FortiGate firewall

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

### Prerequisites

- A working SSLVPN (portal or tunnel) configuration in FortiGate
- A certificate for signing and encryption uploaded to both authentik and FortiGate
- FortiGate version 7.2.8 or later
- authentik version 2024.2.2 or later

## authentik configuration

To support the integration of FortiGate SSLVPN with authentik, you need to create an application/provider pair and user group in authentik.

### Create a user group

1. Log in to authentik as an admin and navigate to the admin Interface.
2. Navigate to **Directory** > **Groups** and click **Create**.
3. Set a descriptive name for the group (e.g. "FortiGate SSLVPN Users").
4. Add the users who should have access to the SSLVPN.
5. Click **Save**.

### Create an application and provider in authentik

1. Log in to authentik as an admin and navigate to the admin Interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair.

- **Application**: provide a descriptive name (e.g. "FortiGate SSLVPN"), an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **SAML Provider from metadata** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), and configure the following required settings:
    - Upload the metadata file from FortiGate (you will get this in the FortiGate configuration steps)
    - Set the **ACS URL** to <kbd>https://<em>fortigate.company</em>/remote/saml/login</kbd>
    - Set the **Audience** to <kbd>http://<em>fortigate.company</em>/remote/saml/metadata/</kbd>
    - Select your signing certificate
    - Under **Advanced Protocol Settings**:
        - Set **Assertion valid not before** to <kbd>minutes=5</kbd>
        - Set **Assertion valid not on or after** to <kbd>minutes=5</kbd>
        - Set **Digest algorithm** to <kbd>sha256</kbd>
        - Set **Signature algorithm** to <kbd>sha256</kbd>
- **Configure Bindings**: create a binding to the user group you created earlier to manage access to the SSLVPN.

3. Click **Submit** to save the new application and provider.

## FortiGate configuration

### Setup SAML SP

1. SSH to the FortiGate (If you are using vdom change to the correct vdom).
2. The configuration will be written to `/data/config/config.conf`. Copy and paste the following configuration, replacing the placeholders with your values:

```
config user saml
    edit "authentik-sso"
        set cert "your-fortigate-cert"
        set entity-id "http://fortigate.company/remote/saml/metadata/"
        set single-sign-on-url "https://fortigate.company/remote/saml/login"
        set single-logout-url "https://fortigate.company/remote/saml/logout"
        set idp-entity-id "https://authentik.company"
        set idp-single-sign-on-url "https://authentik.company/application/saml/fortigate-sslvpn/sso/binding/redirect/"
        set idp-single-logout-url "https://authentik.company/application/saml/fortigate-sslvpn/slo/binding/redirect/"
        set idp-cert "your-authentik-cert"
        set user-name "http://schemas.goauthentik.io/2021/02/saml/username"
        set group-name "http://schemas.xmlsoap.org/claims/Group"
        set digest-method sha256
    next
end
```

### Add SAML SSO to a user group

Configure the FortiGate user group:

```
config user group
    edit "sslvpn-users"
        set member "authentik-sso"
        config match
            edit 1
                set server-name "authentik-sso"
                set group-name "FortiGate SSLVPN Users"
            next
        end
    next
end
```

:::info
Remember to map the user group to a portal in the 'SSL-VPN Settings' page and add it to firewall rules, or users will be redirected back to authentik with a logout immediately upon each login attempt.
:::

### Download SAML metadata

1. Navigate to your FortiGate web interface at <kbd>https://<em>fortigate.company</em></kbd>
2. Go to **User & Authentication** > **SAML** > **Single Sign-On Server**
3. Click on the "authentik-sso" server you created
4. Click **Download** to get the SAML metadata file
5. Return to authentik and upload this metadata file in the provider configuration

## Configuration verification

To verify the integration:

1. Navigate to your FortiGate SSLVPN portal at <kbd>https://<em>fortigate.company</em></kbd>
2. You should be redirected to authentik to authenticate
3. After successful authentication, you should be redirected back to the FortiGate SSLVPN portal
4. Verify that you can establish a VPN connection

:::info
If you encounter any issues:

- Check that the user group bindings are correctly configured in both authentik and FortiGate
- Verify the SAML metadata and certificates are correctly uploaded
- Enable debug logging in FortiGate:
    ```
    diagnose debug enable
    diag debug application samld -1
    ```
- Check the FortiGate logs for SAML-related errors
  :::

## Additional Resources

- [FortiGate SSLVPN Documentation](https://docs.fortinet.com/document/fortigate/7.2.8/administration-guide/397719/ssl-vpn)
- [FortiGate SAML Configuration Guide](https://docs.fortinet.com/document/fortigate/7.2.8/administration-guide/954635/saml-sp)
