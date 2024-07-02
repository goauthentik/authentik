---
title: Zabbix
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Zabbix

> Zabbix is an open-source monitoring software suite that provides monitoring and tracking of metrics, performance, and availability of IT resources.
>
> -- https://www.zabbix.com/features

## Preparation

The following placeholders will be used:

-   `zabbix.company` is the FQDN of the Zabbix install.
-   `authentik.company` is the FQDN of the authentik install.

### authentik configuration

Create a SAML provider with the following parameters:

   -   **ACS URL**: `https://zabbix.company/zabbix/index_sso.php?acs`
   -   **Issuer**: `zabbix`
   -   **Service Provider Binding**: Post

   Customize certificates and durations as needed.

## Zabbix configuration

### Step 1 - Configure SAML Settings in Zabbix

Navigate to `https://zabbix.company/zabbix/zabbix.php?action=authentication.edit` and configure the SAML settings:

-   Enable SAML authentication.
-   Set **IdP entity ID** to `zabbix`.
-   Set **SSO service URL** to `https://authentik.company/application/saml/zabbix/sso/binding/redirect/`.
-   Set **Username attribute** to `http://schemas.goauthentik.io/2021/02/saml/username`.
-   Set **SP entity ID** to `https://authentik.company/application/saml/zabbix/sso/binding/redirect/`.
-   Set **SP name ID format** to `urn:oasis:names:tc:SAML:2.0:nameid-format:transient`.
-   Enable **Case sensitive login**.

### Step 2 - Certificate Configuration

Configure the SAML Service Provider Certificate and Private Key:

-   Copy the certificate (`sp.crt`) and private key (`sp.key`) to `/usr/share/zabbix/conf/certs/`.

   Configure the certificate path in `zabbix.conf.php`:

   ```php
   $SSO['SP_KEY'] = '<path to the SP private key file>';
   $SSO['SP_CERT'] = '<path to the SP cert file>';
```

### Step 3 - Enhance Security

For enhanced security, enable verification certificate:

    Check **Sign -> AuthN requests** in Zabbix configuration.
    Define the IDP certificate path in `zabbix.conf.php`:
    ```php
    $SSO['IDP_CERT'] = '<path to the IDP cert file>';
```