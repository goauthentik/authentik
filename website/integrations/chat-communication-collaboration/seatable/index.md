---
title: Integrate with SeaTable
sidebar_label: SeaTable
support_level: community
---

## What is SeaTable

> SeaTable is a no-code database and app builder platform that provides a web-based, spreadsheet-like interface for organizing data, building apps, and automating workflows. It is designed to function as a collaborative database with features like tables, views, forms, and permissions.
>
> -- https://seatable.com

## Preparation

The following placeholders are used in this guide:

- `seatable.company` is the FQDN of the SeaTable installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info SaaS vs Selfhosted
SeaTable is available as both a cloud SaaS and a self-hosted solution. This guide is for **self-hosters only**. For detailed setup and administration, refer to the [SeaTable Admin Manual](https://admin.seatable.com).
:::

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of SeaTable with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
        - Set the **Launch URL** to `https://seatable.company/sso/`.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://seatable.company/saml/acs/`.
        - Set the **Issuer** to `https://seatable.company`
        - Set the **Service Provider Binding** to `Post`.
        - Set the **Audience** to `https://seatable.company/saml/metadata/`.
        - Under **Advanced protocol settings**, select an available **Signing certificate**
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate and retrieve metadata URL

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the newly created SeaTable provider.
3. Under **Download signing certificate**, click **Download**. This certificate file will be required in the next section.
4. Under **Metadata**, click **Copy download URL**. This metadata download URL will be required in the next section.

## SeaTable configuration

To support the integration of authentik with SeaTable, you need to configure certificates and enable SAML authentication in SeaTable.

### Setup required certificates

1. Connect to you SeaTable server.
2. Create a `/opt/seatable-server/certs` directroy and navigate to it.
3. Copy the signing certificate that you donwloaded from authentik to this directory and name it `idp.crt`.
4. Generate a certificate and key with the following command:

    ```sh
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout sp.key -out sp.crt
    ```

After completing these steps, the `/opt/seatable-server/certs` directory should contain: `idp.crt`, `sp.crt`, and `sp.key`.

### Determine effective URL for metadata download

authentik's **metadata download URL** returns a 302 redirect but SeaTable requires the effective URL. Run the following command to determine the effective URL:

    ```sh
    curl -s -L -o /dev/null -w "%{url_effective}\n" "<metadata_download_URL>" 2>&1 | tail -n1
    ```

The output of this command will be required as the `SAML_REMOTE_METADATA_URL` in the next section.

### Configure SAML authentication

Add the following block to your SeaTable configuration file located at `/opt/seatable-server/seatable/conf/dtable_web_settings.py`.

```python title="/opt/seatable-server/seatable/conf/dtable_web_settings.py"
ENABLE_SAML = True
SAML_PROVIDER_IDENTIFIER = 'authentik'
SAML_REMOTE_METADATA_URL = '<metadata_effective_url>'
SAML_ATTRIBUTE_MAP = {
    'http://schemas.goauthentik.io/2021/02/saml/uid': 'uid',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress': 'contact_email',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name': 'name',
}
SAML_CERTS_DIR = '/shared/certs'
```

Restart the SeaTable service or Docker container to apply the changes.

## Configuration verification

To confirm that Authentik is integrated correctly with SeaTable, log out and navigate to the SeaTable login page. Click the new **Single Sign-On** button and you will be redirected to authentik. Once authenticated you will be logged in to SeaTable.

:::info Troubleshooting
Check `opt/seatable-server/seatable/logs/dtable_web.log` for troubleshooting info if authentication fails.
:::

## Resources

- [SeaTable Admin Manual - SAML](https://admin.seatable.com/configuration/authentication/saml/)
