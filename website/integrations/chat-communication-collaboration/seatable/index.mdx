---
title: Integrate with SeaTable
sidebar_label: SeaTable
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";
import Tabs from "@theme/Tabs";
import TabItem from "@theme/TabItem";

## What is SeaTable?

> SeaTable is a no-code database and app builder platform that provides a web-based, spreadsheet-like interface for organizing data, building apps, and automating workflows. It is designed to function as a collaborative database with features like tables, views, forms, and permissions.
>
> -- https://seatable.com

## Preparation

The following placeholders are used in this guide:

- `seatable.company` is the FQDN of the self-hosted SeaTable installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info SeaTable Cloud and self-hosted SeaTable
SeaTable supports SAML SSO for SeaTable Cloud Enterprise teams and self-hosted SeaTable Server Enterprise Edition installations. SeaTable Cloud requires domain verification in SeaTable Team Management, which is outside the scope of this guide.
:::

For SeaTable Cloud, log in to SeaTable Cloud and navigate to **Team Management** > **Teams** > **Settings** > **Single Sign-On**. Keep the SeaTable-provided **Entity ID**, **Assertion Consumer Service (ACS) URL**, **Login (SSO URL)**, and **Logout** values available while creating the authentik provider.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

<Tabs
defaultValue="saas"
values={[
{ label: "SeaTable Cloud (SaaS)", value: "saas" },
{ label: "Self-hosted SeaTable", value: "self-hosted" },
]}>
<TabItem value="saas">

## authentik configuration

To support the integration of SeaTable Cloud with authentik, you need to create SAML property mappings and an application/provider pair in authentik.

### Create property mappings

SeaTable Cloud requires SAML attributes named `contact_email`, `name`, and `uid`. Create three SAML provider property mappings for these attributes.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the type and click **Next**.
4. Create a property mapping with the following values:
    - **Name**: `SeaTable contact_email`
    - **SAML Attribute Name**: `contact_email`
    - **Expression**:

        ```python
        return request.user.email
        ```

5. Click **Finish** to save the property mapping.
6. Repeat steps 2-5 to create the following additional property mappings:
    - **Name**: `SeaTable name`
    - **SAML Attribute Name**: `name`
    - **Expression**:

        ```python
        return request.user.name
        ```

    - **Name**: `SeaTable uid`
    - **SAML Attribute Name**: `uid`
    - **Expression**:

        ```python
        return request.user.uid
        ```

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because you will use it later as `<application_slug>`.
        - Set the **Launch URL** to the **Login (SSO URL)** value from SeaTable.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to the **Assertion Consumer Service (ACS) URL** value from SeaTable.
        - Set the **Audience** to the **Entity ID** value from SeaTable.
        - Set the **SLS URL** to the **Logout** value from SeaTable.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**:
            - Set an available **Signing certificate**.
            - Add the `SeaTable contact_email`, `SeaTable name`, and `SeaTable uid` property mappings that you created earlier to **Property mappings**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate and retrieve the metadata URL

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the newly created SeaTable provider.
3. Under **Related objects** > **Download signing certificate**, click **Download**. This certificate file will be required in the next section.
4. Under **Related objects** > **Metadata**, click **Copy download URL**. This metadata download URL will be required in the next section.

## SeaTable configuration

To support the integration of authentik with SeaTable Cloud, configure SeaTable with the authentik certificate and metadata URL.

### Determine effective URL for metadata download

authentik's **metadata download URL** returns a 302 redirect, but SeaTable Cloud requires the effective URL. Run the following command to determine the effective URL:

```sh
curl -Ls -o /dev/null -w '%{url_effective}\n' "<metadata_download_URL>" 2>/dev/null
```

The output of this command will be required as the SeaTable metadata URL.

### Configure SeaTable Cloud

1. Log in to SeaTable Cloud and navigate to **Team Management** > **Teams** > **Settings** > **Single Sign-On**.
2. Configure the following settings:
    - **Metadata URL**: enter the effective metadata URL from authentik.
    - **Certificate**: upload or paste the signing certificate that you downloaded from authentik.
    - **Domain**: select the email domain that should use this SSO configuration.
3. Complete the DNS domain verification shown by SeaTable.

</TabItem>

<TabItem value="self-hosted">

## authentik configuration

To support the integration of self-hosted SeaTable with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because you will use it later as `<application_slug>`.
        - Set the **Launch URL** to `https://seatable.company/sso/`.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://seatable.company/saml/acs/`.
        - Set the **Audience** to `https://seatable.company/saml/metadata/`.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**, set an available **Signing certificate**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate and retrieve the metadata URL

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the newly created SeaTable provider.
3. Under **Related objects** > **Download signing certificate**, click **Download**. This certificate file will be required in the next section.
4. Under **Related objects** > **Metadata**, click **Copy download URL**. This metadata download URL will be required in the next section.

## SeaTable configuration

To support the integration of authentik with self-hosted SeaTable, configure SeaTable with the authentik certificate and metadata URL.

### Determine effective URL for metadata download

authentik's **metadata download URL** returns a 302 redirect, but SeaTable requires the effective URL. Run the following command to determine the effective URL:

```sh
curl -Ls -o /dev/null -w '%{url_effective}\n' "<metadata_download_URL>" 2>/dev/null
```

The output of this command will be required as the `SAML_REMOTE_METADATA_URL` in the next section.

### Configure self-hosted SeaTable

#### Set up required certificates

SeaTable requires the signing certificate from authentik and its own signing certificate. Follow these steps to configure the required certificates on your SeaTable deployment.

1. Connect to your SeaTable server or exec into the shell of your SeaTable container.
2. Create the `/opt/seatable-server/certs` directory and navigate to it.
3. Copy the signing certificate that you downloaded from authentik to this directory and name it `idp.crt`.
4. Generate a certificate and key with the following command:

```sh
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout sp.key -out sp.crt
```

After completing these steps, the `/opt/seatable-server/certs` directory should contain: `idp.crt`, `sp.crt`, and `sp.key`.

#### Configure SAML authentication

Add the following block to your SeaTable configuration file:

```python title="/opt/seatable-server/seatable/conf/dtable_web_settings.py"
ENABLE_SAML = True
SAML_PROVIDER_IDENTIFIER = 'authentik'
SAML_REMOTE_METADATA_URL = '<effective metadata download URL from authentik>'
SAML_ATTRIBUTE_MAP = {
    'http://schemas.goauthentik.io/2021/02/saml/uid': 'uid',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress': 'contact_email',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name': 'name',
}
SAML_CERTS_DIR = '/shared/certs'
```

Restart the SeaTable service or Docker container to apply the changes.

</TabItem>

</Tabs>

## Configuration verification

To confirm that authentik is integrated correctly with SeaTable, log out of SeaTable and access SeaTable from the authentik application dashboard. You should be redirected to SeaTable.

:::info Self-hosted troubleshooting
For self-hosted SeaTable, check `/opt/seatable-server/seatable/logs/dtable_web.log` for troubleshooting info if authentication fails.
:::

## Resources

- [SeaTable Admin Manual - SAML](https://admin.seatable.com/configuration/authentication/saml/)
- [SeaTable Help - Requirements and prerequisites for using single sign-on](https://seatable.com/help/requirements-single-sign-on/)
- [SeaTable Help - IdP setup, attribute mapping, and domain authentication](https://seatable.com/help/configuration-ipd-single-sign-on-seatable-cloud/)
