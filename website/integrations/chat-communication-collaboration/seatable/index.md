---
title: Integrate with SeaTable
sidebar_label: SeaTable
support_level: community
---

## What is SeaTable

> SeaTable is a no-code collaborative platform that combines the simplicity of spreadsheets with the power of a flexible database. It enables teams to store, organize, and visualize all types of data in customizable tables and views without the need for programming skills. SeaTable supports real-time collaboration, workflow automation, and integrations, making it ideal for managing projects, tracking assets, and analyzing data efficiently, whether deployed in the cloud or on-premises.
>
> -- https://seatable.com

:::info
SeaTable is available as both a cloud SaaS and a self-hosted solution. This guide is for **self-hosters only**. For detailed setup and administration, see the SeaTable Admin Manual at https://admin.seatable.com.
:::

## Preparation

The following placeholders are used in this guide:

- `seatable.company` is the FQDN of the SeaTable installation. (Remove this for SaaS)
- `authentik.company` is the FQDN of the authentik installation.

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
    - **Choose a Provider type**: select **SAML Provider** as the provider type
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
      - Set the **ACS URL** to `https://seatable.company/saml/acs/`.
      - Set the **Issuer** to `https://seatable.company`
      - Set the **Service Provider Binding** to `Post`.
      - Set the **Audience** to `https://seatable.company/saml/metadata/`.
      - Under **Advanced protocol settings**, select an available **Signing certificate**
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Retrieve provider metadata

1. From the authentik Admin interface, navigate to **Applications > Providers** and select the SeaTable SAML provider.
2. In the **Related Objects** section:
   1. click **Copy download URL** to copy the metadata URL to your clipboard. Paste this URL into a text editor as you will need it when configuring SAML in SeaTable.
   2. Download the **signing certificate** as well.

## SeaTable configuration

To enable SAML authentication in SeaTable, access your SeaTable Server's command line and follow these steps:

### Certificates

1. Create the directory `/opt/seatable-server/certs` and navigate into it.
2. Save the **signing certificate** you downloaded from authentik into this directory and name it `idp.crt`.
3. Generate a certificate and key with the following command:

```sh
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout sp.key -out sp.crt
```

After completion, the directory `/opt/seatable-server/certs` should contain: `idp.crt`, `sp.crt`, and `sp.key`.

### Activate SAML

Since authentik's **metadata download URL** returns a 302 redirect, resolve the actual URL by running:

```sh
export AUTHENTIK_DOWNLOAD_URL=<your-authentik-metatadata-url-save-in-your-text-editor>
curl -I ${AUTHENTIK_DOWNLOAD_URL}
```

Next, edit the configuration file `/opt/seatable-server/seatable/conf/dtable_web_settings.py` and add the following block. The only value you have to change is the `SAML_REMOTE_METADATA_URL`.

```python
ENABLE_SAML = True
SAML_PROVIDER_IDENTIFIER = 'authentik'
SAML_REMOTE_METADATA_URL = ''
SAML_ATTRIBUTE_MAP = {
    'http://schemas.goauthentik.io/2021/02/saml/uid': 'uid',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress': 'contact_email',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name': 'name',
}
SAML_CERTS_DIR = '/shared/certs'
```

Restart the SeaTable service or Docker container to apply the changes.

## Configuration verification

To confirm that Authentik is integrated correctly with SeaTable, log out and navigate to the SeaTable login page. Click the new **Single Sign-On** button. If the setup is successful, you will be redirected to authentik’s login page. After authenticating, you should gain access to SeaTable. 

Check `opt/seatable-server/seatable/logs/dtable_web.log` for troubleshooting info if authentication fails.

## Additional Resources

```text
- [SeaTable Admin Manual: Single-Node Deployment](https://admin.seatable.com/installation/basic-setup/)
- [SeaTable ADmin Manual: SAML](https://admin.seatable.com/configuration/authentication/saml/)
```
