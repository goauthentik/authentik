---
title: Integrate with Mautic
sidebar_label: Mautic
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Mautic?

> Mautic provides free and open source marketing automation software available to everyone. Free email marketing and lead management software.
>
> -- https://mautic.org/

## Preparation

The following placeholders are used in this guide:

- `mautic.company` is the FQDN of the Mautic installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Mautic with authentik, create two SAML property mappings and an application/provider pair in authentik.

### Create property mappings

Mautic requires first name and last name attributes in the SAML response. Create two [SAML provider property mappings](/docs/users-sources/sources/property-mappings):

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** and click **Next**.
4. Configure the property mapping with the following settings:
    - **Name**: `SAML-FirstName-from-Name`
    - **SAML Attribute Name**: `FirstName`
    - **Friendly Name**: leave blank.
    - **Expression**:

        ```python
        names = request.user.name.split(" ", 1)
        if len(names) == 1:
            return request.user.name
        return names[0]
        ```

5. Click **Finish** to save the property mapping.
6. Again, navigate to **Customization** > **Property Mappings** and click **Create**.
7. Select **SAML Provider Property Mapping** and click **Next**.
8. Configure the property mapping with the following settings:
    - **Name**: `SAML-LastName-from-Name`
    - **SAML Attribute Name**: `LastName`
    - **Friendly Name**: leave blank.
    - **Expression**:

        ```python
        return request.user.name.split(" ", 1)[-1]
        ```

9. Click **Finish** to save the property mapping.

### Create an application and provider pair

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** value because it is required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set **ACS URL** to `https://mautic.company/s/saml/login_check`.
        - Set **Audience** to `https://mautic.company`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Enable **Sign responses**.
            - Add `SAML-FirstName-from-Name` and `SAML-LastName-from-Name` to **Selected User Property Mappings**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.

### Download the metadata

1. Navigate to **Applications** > **Providers** and click the name of the SAML provider that you created.
2. Under **Metadata**, click **Download** to save the metadata XML file. This file is required in the next section.

## Mautic configuration

If Mautic runs behind an SSL-terminating reverse proxy, first navigate to **Configuration** > **System Settings** in Mautic and make sure that:

- the **Site URL** starts with `https://`
- **Trusted proxies** includes the IP address of the reverse proxy

Then configure SAML in Mautic:

1. Log in to Mautic as an administrator.
2. Click the settings cogwheel in the top-right corner.
3. Navigate to **Configuration** > **User/Authentication Settings**.
4. In **SAML SSO Settings**, set the following values:
    - **Entity ID for the IDP**: select `https://mautic.company`.
    - **Identity provider metadata file**: upload the metadata XML file from authentik.
    - **Default role for created users**: select the role to assign to users created through SAML login. Leave this empty only if all SAML users already exist in Mautic.
    - **Email**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
    - **Username**: `http://schemas.goauthentik.io/2021/02/saml/username`
    - **First name**: `FirstName`
    - **Last name**: `LastName`
5. Click **Save**.

Leave **X.509 certificate** and **Private key** unset unless you intentionally configure Mautic with its own SAML certificate and stricter SAML trust options. Those fields are for a Mautic-owned certificate and private key, not for authentik's signing key. If you configure them, also configure the matching verification and encryption settings in authentik.

### Common SAML errors

The following errors usually indicate a mismatch between authentik and Mautic configuration:

- `Uncaught PHP Exception TypeError: "Mautic\UserBundle\Entity\User::getUserIdentifier(): Return value must be of type string, null returned"`: Mautic did not receive the expected email or username attribute. Check the **Email**, **Username**, **First name**, and **Last name** attribute names in Mautic and the selected property mappings in authentik.
- `Unable to verify Signature`: the metadata file uploaded to Mautic does not match the signing certificate currently used by the authentik SAML provider. Download the provider metadata again and upload the new file to Mautic.
- `Assertions must be signed`: the authentik SAML provider does not have a **Signing Certificate** selected, or **Sign assertions** is not enabled.
- `Private key is invalid. It should begin with -----BEGIN RSA PRIVATE KEY----- or -----BEGIN ENCRYPTED PRIVATE KEY-----`: Mautic rejected a private key uploaded to its **Private key** field. Leave the field unset unless you intentionally configure Mautic with its own SAML certificate and stricter SAML trust options.

## Configuration verification

To confirm that authentik is properly configured with Mautic, open Mautic in a new incognito/private window or another browser and log in. Using a separate browser session lets you keep access to the Mautic configuration interface if the SAML login fails.

## Resources

- [Mautic documentation - SAML/SSO settings](https://docs.mautic.org/en/7.0/configuration/settings.html#saml-sso-settings)
- [Mautic documentation - Authentication](https://docs.mautic.org/en/4.x/authentication/authentication.html#saml)
