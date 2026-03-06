---
title: Integrate with Splunk Enterprise
sidebar_label: Splunk Enterprise
support_level: community
---

## What is Splunk Enterprise

> Splunk's core offering collects and analyzes high volumes of machine-generated data. It uses a lightweight agent to locally collect log messages from files, receives them via TCP or UDP syslog protocol on an open port (not preferred), or calls scripts to collect events from various application programming interfaces (APIs) to connect to applications and devices.
> It was developed for troubleshooting and monitoring distributed applications based on log messages.
>
> -- https://en.wikipedia.org/wiki/Splunk#Products

The following placeholders will be used in the examples below:

- `authentik.company` is the FQDN of the authentik installation.
- `splunk.company` is the FQDN of the Splunk Enterprise instance.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Splunk Enterprise with authentik, you need to create an application and provider pair, a self-signed certificate, and a custom property mapping in authentik.

### Create and import a self-signed certificate

The certificates generated under **System** > **Certificates** are issued by a certificate authority (CA) and not self-signed. To work around this, create a custom self-signed certificate and import it. See [issue 19058 for reference](https://github.com/goauthentik/authentik/issues/19058).

1. On your workstation, generate the certificate using openssl:
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 36500 -nodes -subj "/O=company/OU=authentik/CN=authentik.company"
```
2. Log in to authentik as an administrator and open the Admin interface.
3. Navigate to **System** > **Certificates**.
4. Click **Import**. Give the certificate a unique name, paste the contents of `cert.pem` into the **Certificate** field, and paste the contents of `key.pem` into the **Private Key** field. Click **Import**.

### Create custom property mapping

Splunk expects user groups in the `roles` field. Create a custom property mapping to support this.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**
3. In the wizard select **SAML Provider Property Mapping** and click **Next**
4. In the following page enter
    - A unique **Name**
    - `role` as **SAML Attribute Name**
    - Use the Python expression below for the **Expression** field and click **Save**.
```python
return [g.name for g in user.ak_groups.all()]
```

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively, you can create a provider separately first, then create the application and connect it with the provider. This allows you to import the XML metadata file from Splunk.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://spunk.company:8000/saml/acs`.
        - Set the **Issuer** to `https://authentik.company`.
        - Set the **Audience** to `https://splunk.company:8000`.
        - Set the **SLS URL** to `https://splunk.company:8000/saml/logout`.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced Flow Settings** select a **Invalidation flow**.
        - Under **Advanced protocol settings**, set **Signing Certificate** to the certificate that you imported in the previous step.
        - Activate **Sign assertions** and **Sign responses**.
        - Select the same certificate in **Verification Certificate**.
        - In **Property Mappings**, add the mapping that you created and remove `authentik default SAML Mapping: Groups`.
        - If you want the username in Splunk to match the username in authentik rather than the long `Subject` ID, select `authentik default SAML Mapping: username` in **NameID Property Mapping**.
        - Click **Next**.
    - **Configure Bindings** _(optional)_: You can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.
3. Click **Submit** to save the new application and provider.
4. Open the provider and in the **Related objects** section, click **Download** to download the **Metadata** file and the **Signing Certificate**.


## Splunk Enterprise configuration

### SAML configuration

1. Log in to Splunk Enterprise with your local administrator account. Using the Splunk bar, navigate to **Settings** > **USERS AND AUTHENTICATION** > **Authentication methods**.
2. Select **SAML** as the external authentication method and click **Configure Splunk to use SAML**.
3. Click the **SAML Config** button in the top right.

:::warning Lockout
Errors in the following step can result in account lockout. Note the Local access URL by using the **Copy Link** button in the warning banner. The URL is typically https://splunk.company:8000/en-US/account/login?loginType=Splunk. If you still cannot access your account, remove the file `/opt/splunk/etc/system/local/authentication.conf` on your Splunk server and restart.
:::

5. Configure the SAML settings:
    - Upload the metadata file from authentik by dragging it into the drop zone or by pasting the content into the **Metadata contents** text area.
    - Enter https://splunk.company:8000 as **Entity ID**. This value must match the **Audience** value in authentik.
    - Copy the content of the Signing Certificate (starting with `-----BEGIN CERTIFICATE-----`) into the **IdP certificate chains** field.
    - In **Advanced Settings**, set **Load balancer hostname or IP address** to https://splunk.company.
6. Click **Save**.

### Configure group mappings
Splunk Enterprise can map groups from authentik to its internal roles. In the default configuration, groups and roles with the same name are automatically mapped. For example, if you have a group `users` in authentik, members are mapped to the `users` role in Splunk. 

To map a custom group, follow these steps:
1. Log in to Splunk Enterprise with your local administrator account. Using the Splunk bar, navigate to **Settings** > **USERS AND AUTHENTICATION** > **Authentication methods**.
2. Click **Configure Splunk to use SAML**.
3. In the top right, click **New Group**.
4. Configure your mapping:
    - **Group name**: Specify the group name as it appears in authentik.
    - **Splunk roles**: Select and assign the Splunk roles that you want to assign to this group.
5. Click **Save**.

## Configuration Verification

To verify the integration, log out of Splunk Enterprise and open https://splunk.company:8000 in a new tab. If the configuration is correct, you will be redirected to the authentik login screen. After logging in, you will be returned to Splunk Enterprise.

## Resources

- [Splunk Enterprise Documentation - Configure single signon with SAML](https://help.splunk.com/en/splunk-enterprise/administer/manage-users-and-security/10.2/use-saml-as-an-authentication-scheme-for-single-sign-on/configure-single-sign-on-with-saml)
- [Splunk Enterprise Documentation - Configure SAML SSO for other IdPs](https://help.splunk.com/en/splunk-enterprise/administer/manage-users-and-security/10.2/use-saml-as-an-authentication-scheme-for-single-sign-on/configure-saml-sso-for-other-idps)
- [Splunk Enterprise Documentation. Troubleshooting SAML SSO](https://help.splunk.com/en/splunk-enterprise/administer/manage-users-and-security/10.2/use-saml-as-an-authentication-scheme-for-single-sign-on/troubleshoot-saml-sso)
