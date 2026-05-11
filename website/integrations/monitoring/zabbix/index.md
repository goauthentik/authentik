---
title: Integrate with Zabbix
sidebar_label: Zabbix
support_level: community
---

## What is Zabbix?

> Zabbix is the ultimate enterprise-level software designed for real-time monitoring of millions of metrics collected from tens of thousands of servers, virtual machines and network devices.
>
> Zabbix is Open Source and comes at no cost.
>
> -- https://www.zabbix.com/features

## Preparation

The following placeholders are used in this guide:

- `zabbix.company` is the FQDN of the Zabbix installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Zabbix with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to `https://zabbix.company/index_sso.php?acs`.
    - Set the **Audience** to `https://zabbix.company/zabbix`.
    - Set the **Single Logout Service** to `https://zabbix.company/index_sso.php?sls`.
    - Set the **SLS Binding** to `Redirect`.
    - Set the **Logout Method** to `Front-channel (Iframe)`.
    - Under **Advanced protocol settings**, select an available **Signing certificate**.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Zabbix configuration

Navigate to `https://zabbix.company/zabbix/zabbix.php?action=authentication.edit` and select SAML settings to configure SAML.

Check the box to enable SAML authentication.

Set the Field **IdP entity ID** to `https://authentik.company/application/saml/zabbix/metadata/`.

Set the Field **SSO service URL** to `https://authentik.company/application/saml/zabbix/`.

Set the Field **Username attribute** to `http://schemas.goauthentik.io/2021/02/saml/username`.

Set the Field **SP entity ID** to `https://zabbix.company/zabbix`.

Set the Field **SP name ID format** to `urn:oasis:names:tc:SAML:2.0:nameid-format:transient`.

Check the box for **Case sensitive login**.

### Verify signed responses

To configure Zabbix to verify responses from authentik:

1. Download the authentik signing certificate from the SAML provider page and place it in `/usr/share/zabbix/conf/certs/` under the name `idp.crt`.

### Configure SP certificates _(optional)_

Zabbix uses an SP private key to sign its SAML AuthN requests. Generate a dedicated self-signed pair for Zabbix:

1. Generate the SP key and certificate:

    ```bash
    openssl req -new -x509 -days 3650 -nodes \
        -subj "/CN=zabbix.company" \
        -keyout sp.key -out sp.crt
    ```

2. Copy the files to `/usr/share/zabbix/conf/certs/`. By default Zabbix looks for `sp.crt` and `sp.key`.
3. In the Zabbix SAML configuration, enable **Sign** > **AuthN requests**.
