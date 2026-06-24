---
title: Integrate with Zabbix
sidebar_label: Zabbix
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Zabbix?

> Zabbix is an enterprise-class open source observability solution.
>
> -- https://www.zabbix.com

## Preparation

The following placeholders are used in this guide:

- `zabbix.company` is the FQDN of the Zabbix installation.
- `authentik.company` is the FQDN of the authentik installation.

This guide assumes that the Zabbix frontend is available at `https://zabbix.company/zabbix`. If your Zabbix frontend uses a different path, adjust every Zabbix URL in this guide to match your public frontend URL.

:::info Prerequisites
Zabbix requires `php-openssl` for SAML authentication. You also need access to the Zabbix frontend `conf/certs` directory to add the authentik signing certificate.
:::

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Zabbix with authentik, you need to create an application/provider pair in authentik.

If you want Zabbix to create users during their first SAML login, you also need to create SAML property mappings for users' given names and surnames.

### Create JIT property mappings in authentik _(optional)_

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings**, click **Create**, select **SAML Provider Property Mappings**, and click **Next**.
3. Configure the first mapping for the user's given name:
    - **Name**: `givenname`
    - **SAML Attribute Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname`
    - **Friendly Name**: Leave blank
    - **Expression**:

    ```python
    return request.user.name.split(" ", 1)[0]
    ```

4. Click **Finish** to save the mapping.
5. Repeat the process to create a mapping for the user's surname:
    - **Name**: `surname`
    - **SAML Attribute Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname`
    - **Friendly Name**: Leave blank
    - **Expression**:

    ```python
    return request.user.name.rsplit(" ", 1)[-1]
    ```

6. Click **Finish**.

### Create an application and provider in authentik

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because you will use it when configuring Zabbix.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - **ACS URL**: `https://zabbix.company/zabbix/index_sso.php?acs`
        - **Audience**: `https://zabbix.company/zabbix`
        - **SLS URL**: `https://zabbix.company/zabbix/index_sso.php?sls`
        - **SLS Binding**: `Redirect`
        - **Logout Method**: `Front-channel (Iframe)`
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - If you want to use Zabbix JIT provisioning, under **Property mappings**, add the `givenname` and `surname` mappings that you created in the previous section.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate

1. Navigate to **Applications** > **Providers** and open the provider that you created.
2. Under **Related objects** > **Download signing certificate**, click **Download**.
3. Save the downloaded certificate as `idp.crt` in the Zabbix frontend `conf/certs` directory, for example `/usr/share/zabbix/conf/certs/idp.crt`.

## Zabbix configuration

1. Log in to Zabbix as an administrator.
2. Navigate to **Users** > **Authentication**, then select the **SAML settings** tab.
3. Enable SAML authentication.
4. Configure the following fields:
    - **IdP entity ID**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **SSO service URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **SLO service URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **Username attribute**: `http://schemas.goauthentik.io/2021/02/saml/username`
    - **SP entity ID**: `https://zabbix.company/zabbix`
    - **SP name ID format**: `urn:oasis:names:tc:SAML:2.0:nameid-format:transient`
5. Click **Update** to save the configuration.

### Enable JIT provisioning _(optional)_

To provision Zabbix users during their first SAML login, create the required Zabbix user groups and user roles before enabling JIT provisioning. Create one or more Zabbix user groups and user roles whose combinations match the authentik groups that should have access to Zabbix.

If you do not want to use the Zabbix `disabled` group for deprovisioned users, create a dedicated disabled Zabbix user group before continuing.

1. Navigate to **Users** > **Authentication**, then select the **Authentication** tab.
2. Set **Deprovisioned users group** to `disabled`, or to the disabled Zabbix user group that you created for deprovisioned users.
3. Select the **SAML settings** tab.
4. Enable **Enable JIT provisioning** and **Configure JIT provisioning**.
5. Configure the following JIT fields:
    - **Group name attribute**: `http://schemas.xmlsoap.org/claims/Group`
    - **User name attribute**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname`
    - **User last name attribute**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname`
6. Under **User group mapping**, click **Add** and configure a mapping:
    - **SAML group pattern**: enter the name of the authentik group to map.
    - **User groups**: select the Zabbix user groups that members of the authentik group should receive.
    - **User role**: select the Zabbix user role that members of the authentik group should receive.
7. Click **Add** to save the mapping, then repeat the previous step for each authentik group that you want to map to Zabbix user groups and roles.
8. Under **Media type mapping**, click **Add** and configure the email mapping:
    - **Name**: `Email`
    - **Media type**: select `Email` or `Email (HTML)`.
    - **Attribute**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
9. Click **Add** to save the media type mapping.
10. Click **Update** to save the SAML settings.

### Sign Zabbix authentication requests

To have Zabbix sign SAML AuthN requests, generate a certificate and private key for Zabbix:

```bash
openssl req -new -x509 -days 3650 -nodes \
    -subj "/CN=zabbix.company" \
    -keyout sp.key -out sp.crt
```

Copy `sp.key` and `sp.crt` to the Zabbix frontend `conf/certs` directory, then enable **Sign** > **AuthN requests** in the Zabbix SAML settings.

To make authentik require this signature, upload `sp.crt` in authentik under **System** > **Certificates**, then edit the Zabbix SAML provider and select that certificate as the **Verification Certificate**.

### Configure reverse proxy deployments

If Zabbix is behind an HTTPS-terminating reverse proxy and SAML requests are generated with an internal HTTP URL, configure the Zabbix frontend with the public base URL:

```php title="conf/zabbix.conf.php"
$SSO['SETTINGS'] = [
    'strict' => false,
    'baseurl' => 'https://zabbix.company/zabbix/',
    'use_proxy_headers' => true
];
```

## Configuration verification

To confirm that authentik is properly configured with Zabbix, log out of Zabbix and click **Sign in with Single Sign-On (SAML)**. You should be redirected to authentik to log in, then redirected back to Zabbix.

## Resources

- [Zabbix SAML authentication documentation](https://www.zabbix.com/documentation/current/en/manual/web_interface/frontend_sections/users/authentication/saml)
- [Zabbix authentication documentation](https://www.zabbix.com/documentation/current/en/manual/web_interface/frontend_sections/users/authentication)
- [Zabbix SAML setup with Microsoft Entra ID](https://www.zabbix.com/documentation/current/en/manual/appendix/install/azure_ad)
