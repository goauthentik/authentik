---
title: Integrate with Joplin Server
sidebar_label: Joplin
support_level: community
---

## What is Joplin Server?

> Joplin is an open source note-taking app. Capture your thoughts and securely access them from any device.
>
> -- https://joplinapp.org/

Joplin Server is the self-hosted sync service for Joplin clients.

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

Joplin requires SAML assertions to include `email` and `displayName` attributes.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create two **SAML Provider Property Mapping**s with the following settings:
    - **Display name mapping**:
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `displayName`
        - **Expression**:
            ```py
            return request.user.name
            ```
    - **Email mapping**:
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `email`
        - **Expression**:
            ```py
            return request.user.email
            ```

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Set the **Launch URL** to `https://joplin.company/login/sso-saml`. Note the application **Slug** because you will use it later as `<application_slug>`.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - **ACS URL**: `https://joplin.company/api/saml`
        - **Audience**: `<application_slug>`
        - Under **Advanced protocol settings**, select an available **Signing Certificate**, enable **Sign assertions** and **Sign responses**, and add the two property mappings created in the previous section.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Download metadata file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the Joplin provider created in the previous section.
3. In the **Related objects** section, under **Metadata**, click **Download** to save the metadata XML file. You will use this file as the Joplin IdP configuration.

## Joplin configuration

To configure Joplin with authentik, create two SAML configuration files and set the appropriate environment variables.

### Create the Service Provider configuration file

1. Log in to your Joplin server and create a Service Provider (SP) configuration file. Set `entityID` to the authentik application slug.
2. Create the following file in a location that Joplin Server can read, such as a mounted volume:

```xml title="/path/to/joplin-sp.xml"
<?xml version="1.0"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" entityID="<application_slug>">
  <md:SPSSODescriptor AuthnRequestsSigned="false" WantAssertionsSigned="false" protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
    <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
      Location="https://joplin.company/api/saml"
      index="1" />
  </md:SPSSODescriptor>
</md:EntityDescriptor>
```

3. Transfer the metadata XML file downloaded from authentik to your Joplin server, for example as `/path/to/joplin-idp.xml`.

### Configure Joplin environment variables

1. Set the following environment variables. Replace `/path/to/` with the file paths where you saved the SAML configuration files. Joplin Server requires `APP_BASE_URL` and `API_BASE_URL` to use the same URL when SAML is enabled.

```env title=".env"
SAML_ENABLED=true
SAML_IDP_CONFIG_FILE=/path/to/joplin-idp.xml
SAML_SP_CONFIG_FILE=/path/to/joplin-sp.xml
APP_BASE_URL=https://joplin.company
API_BASE_URL=https://joplin.company
DELETE_EXPIRED_SESSIONS_SCHEDULE=
LOCAL_AUTH_ENABLED=false
```

2. Restart Joplin to apply the changes.

## Configuration verification

To confirm that authentik is properly configured with Joplin Server, open Joplin and sign in with SSO. After a successful authentik login, you should be returned to Joplin with access to your notes.

## Resources

- [Joplin Server – SAML configuration](https://joplinapp.org/help/apps/server/saml/)
