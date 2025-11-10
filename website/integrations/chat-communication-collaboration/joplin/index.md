---
title: Integrate with Joplin Server
sidebar_label: Joplin
support_level: community
---

## What is Joplin Server

> Joplin is an open source note-taking app. Capture your thoughts and securely access them from any device.
>
> -- https://joplinapp.org/

 Joplin Server is the self-hosted component that let's you host the server component to sync notes between your devices.

## Preparation

The following placeholders are used in this guide:

- `joplin.company` is the FQDN of the Joplin instance.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Joplin with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create** to create a new mapping, needed for Joplin.

- Select **SAML Provider Property Mapping**.
- Provide a **Name** and a **Firendly Name**.
- Set the **SAML Attribute Name** as `displayName`
- Set the **Expression** as `return user.name`.
- Click **Finish** to save the Mapping.
- Create another Mapping as well.
- Set the **SAML Attribute Name** as `email`.
- Set the **Expression** as `return user.email`.
- Click **Finish** to save the Mapping.

2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Set the **ACS URL** to `https://joplin.company/api/saml`.
    - Set the **Issuer** to `authentik`.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, select an available **Signing certificate**.
    - Enable **Sign assertions**.
    - Enable **Sign responses**.
    - Under **Property mappings**, enable both recently created property mapping for `email` and `displayName`.
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider. Once saved, click the **Download** button under **Related objects** and **Metadata**, this file will be needed by Joplin!

## Joplin Configuration

Joplin needs 2 configuration files in order to make SAML authentication work.
The SP File needs to reflect the `entityID`, that is the string set in the **slug**. Additionally, the ACS URL also needs to be set.

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

Save this file somewhere, where Joplin can read it. This is the IDP Config File.

The second confiruation file will be the file downloaded from authentik. Note the path for this file as well.
When using the container installation of Joplin, set the following environment variables. Use the path where the files above were saved:

```bash
SAML_ENABLED="true"
SAML_IDP_CONFIG_FILE=/joplin-idp.xml
SAML_SP_CONFIG_FILE=/joplin-sp.xml
APP_BASE_URL=https://joplin.company
API_BASE_URL=https://joplin.company
DELETE_EXPIRED_SESSIONS_SCHEDULE=""
```

If local authentication shall be turned off completely, set also:

```bash
LOCAL_AUTH_ENABLED="false"
```

:::info
Remember to restart Joplin after the changes.
:::

## Additional Resources

Please refer to the following for further information:

- https://joplinapp.org/help/apps/server/saml/
