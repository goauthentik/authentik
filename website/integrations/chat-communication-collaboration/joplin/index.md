---
title: Integrate with Joplin Server
sidebar_label: Joplin
support_level: community
---

## What is Joplin Server

> Joplin is an open source note-taking app. Capture your thoughts and securely access them from any device.
>
> -- https://joplinapp.org/

Joplin Server is a self-hosted service that lets you sync notes between your devices.

## Preparation

The following placeholders are used in this guide:

- `joplin.company` is the FQDN of the Joplin installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Joplin with authentik, you need to create property mappings and an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create two **SAML Provider Property Mapping**s with the following settings:
    - **Display Name Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `displayName`
        - **Friendly Name**: Leave blank
        - **Expression**:
        ```python
        return request.user.name
        ```
    - **Email Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `email`
        - **Friendly Name**: Leave blank
        - **Expression**:
        ```python
        return request.user.email
        ```

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to `https://joplin.company/api/saml`.
    - Set the **Issuer** to `authentik`.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, select an available **Signing certificate** and ensure **Sign assertions** and **Sign responses** are enabled.
    - Under **Property mappings**, add the two property mappings created in the previous section.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Retrieve provider metadata

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the Joplin provider created in the previous section.
3. In the **Related Objects** section, click **Download** to save the metadata XML file to your local machine. This file will be needed in the next section.

## Joplin configuration

To configure Joplin with authentik, create two SAML configuration files and set the appropriate environment variables.

### Create the Service Provider configuration file

1. Log in to your Joplin server and create a Service Provider (SP) configuration file. The `entityID` should match the **slug** value from the authentik application.
2. Create a file at `/path/to/joplin-sp.xml` (replace `/path/to/` with the actual directory path where Joplin can read files, such as `/opt/joplin/config/` or a mounted volume in your Docker setup) with the following contents:

```xml
<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="joplin">
  <md:SPSSODescriptor AuthnRequestsSigned="false" WantAssertionsSigned="false" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="https://joplin.company/api/saml"
      index="1" />
  </md:SPSSODescriptor>
</md:EntityDescriptor>
```

3. Transfer the metadata XML file downloaded from authentik to your Joplin server at `/path/to/joplin-idp.xml` (use the same directory as above).

### Configure Joplin environment variables

1. Set the following environment variables. Replace `/path/to/` with the actual file paths where you saved the configuration files:

```bash
SAML_ENABLED="true"
SAML_IDP_CONFIG_FILE=/path/to/joplin-idp.xml
SAML_SP_CONFIG_FILE=/path/to/joplin-sp.xml
APP_BASE_URL=https://joplin.company
API_BASE_URL=https://joplin.company
DELETE_EXPIRED_SESSIONS_SCHEDULE=""
# Optional: Disable local authentication to require SAML login
LOCAL_AUTH_ENABLED="false"
```

2. Restart Joplin to apply the changes.

## Configuration verification

To confirm that authentik is properly configured with Joplin Server, log out of Joplin and then attempt to sign in again. The login page should redirect you to authentik; after a successful authentik login you should be returned to Joplin with access to your notes.

## References

- [Joplin Server – SAML configuration](https://joplinapp.org/help/apps/server/saml/)
