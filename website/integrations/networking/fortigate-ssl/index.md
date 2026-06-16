---
title: Integrate with FortiGate SSL VPN
sidebar_label: FortiGate SSL VPN
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is FortiGate SSL VPN?

> FortiGate is Fortinet's next-generation firewall. Its SSL VPN feature lets remote users connect to protected network resources through a FortiGate firewall.
>
> -- https://www.fortinet.com/products/next-generation-firewall

## Preparation

The following placeholders are used in this guide:

- `fortigate.company` is the FQDN of your FortiGate SSL VPN.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

### Prerequisites

- A working FortiGate SSL VPN configuration.
- A FortiGate local certificate to use for the SAML service provider (SP).
- An authentik certificate to use for signing SAML responses.

## authentik configuration

To support the integration of FortiGate SSL VPN with authentik, you need to create an application/provider pair in authentik.

### Create a user group

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Groups** and click **Create**.
3. Set a descriptive name for the group, for example `FortiGate SSL VPN Users`.
4. Add the users who should have access to FortiGate SSL VPN.
5. Click **Save**.

### Create an application and provider in authentik

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://fortigate.company/remote/saml/login`.
        - Set the **Audience** to `https://fortigate.company/remote/saml/metadata`.
        - Set the **SLS URL** to `https://fortigate.company/remote/saml/logout`.
        - Under **Advanced protocol settings**:
            - Set **Signing Certificate** to the certificate authentik should use to sign SAML responses.
            - Enable **Sign responses**.
    - **Configure Bindings**: create a [binding](/docs/add-secure-apps/bindings-overview/) to the FortiGate SSL VPN user group.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the FortiGate SSL VPN provider.
3. Click **Download** under **Download signing certificate**. You will import this certificate into FortiGate.

## FortiGate configuration

### Import the authentik signing certificate

1. Log in to the FortiGate administrative interface.
2. Navigate to **System** > **Certificates**.
3. Select **Create/Import** > **Remote Certificate**.
4. Upload the authentik signing certificate you downloaded earlier.
5. Note the certificate name that FortiGate assigns to the imported certificate.

### Create the SAML single sign-on server

SSH into FortiGate and run the following commands, replacing `authentik-signing-certificate` with the imported authentik certificate name and `Fortinet_Factory` with the FortiGate local certificate that FortiGate should use as the SP certificate.

```text
config user saml
    edit "authentik-sso"
        set cert "<Your Fortinet Cert>"
        set entity-id "https://fortigate.company/remote/saml/metadata"
        set single-sign-on-url "https://fortigate.company/remote/saml/login"
        set single-logout-url "https://fortigate.company/remote/saml/logout"
        set idp-entity-id "https://authentik.company/application/saml/<application_slug>/metadata/"
        set idp-single-sign-on-url "https://authentik.company/application/saml/<application_slug>/"
        set idp-single-logout-url "https://authentik.company/application/saml/<application_slug>/"
        set idp-cert "authentik-signing-certificate"
        set user-name "http://schemas.goauthentik.io/2021/02/saml/username"
        set group-name "http://schemas.xmlsoap.org/claims/Group"
        set digest-method sha256
    next
end
```

### Create the FortiGate user group

Run the following commands, replacing `FortiGate SSL VPN Users` with the exact name of the authentik group whose members should have VPN access.

```text
config user group
    edit "sslvpn-users"
        set member "authentik-sso"
        config match
            edit 1
                set server-name "authentik-sso"
                set group-name "FortiGate SSL VPN Users"
            next
        end
    next
end
```

### Add the group to SSL VPN

1. In the FortiGate administrative interface, navigate to **VPN** > **SSL-VPN Settings**.
2. In the **Authentication/Portal Mapping** table, create a mapping for the `sslvpn-users` group and select the SSL VPN portal that group should use.
3. Apply your changes.
4. Ensure that the SSL VPN firewall policy includes the `sslvpn-users` group.

If users are redirected back to authentik with an immediate logout after authentication, confirm that the FortiGate user group is mapped to an SSL VPN portal and included in the relevant firewall policy.

## Configuration verification

To confirm that authentik is properly configured with FortiGate SSL VPN, open the FortiGate SSL VPN portal. You should be redirected to authentik to authenticate, and then redirected back to the FortiGate SSL VPN portal.

If you use FortiClient tunnel mode, enable **Enable Single Sign On (SSO) for VPN Tunnel** in the FortiClient SSL VPN connection settings.

## Troubleshooting

To enable SAML debug logging in FortiGate, run the following commands:

```text
diagnose debug console timestamp enable
diagnose debug application samld -1
diagnose debug enable
```

Check that the `user-name` and `group-name` values in FortiGate exactly match the SAML attribute names sent by authentik, and that the FortiGate user group match uses the exact authentik group name.

## Resources

- [Fortinet - Configuring SAML SSO](https://docs.fortinet.com/document/fortigate/8.0.0/administration-guide/254248/configuring-saml-sso)
- [Fortinet - Configuring SAML SSO login for SSL VPN with Entra ID acting as SAML IdP](https://docs.fortinet.com/document/fortigate-public-cloud/8.0.0/azure-administration-guide/584456/configuring-saml-sso-login-for-ssl-vpn-with-entra-id-acting-as-saml-idp)
- [Fortinet - Configuring SAML SSO in the GUI](https://docs.fortinet.com/document/fortigate/7.0.0/new-features/989067/configuring-saml-sso-in-the-gui-7-0-2)
- [Fortinet - Remote certificate](https://docs.fortinet.com/document/fortigate/8.0.0/administration-guide/212403/remote-certificate)
