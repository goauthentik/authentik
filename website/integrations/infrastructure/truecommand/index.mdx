---
title: Integrate with TrueNAS TrueCommand
sidebar_label: TrueNAS TrueCommand
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is TrueNAS TrueCommand?

> TrueCommand is a ZFS-aware solution allowing you to set custom alerts on statistics like ARC usage or pool capacity and ensuring storage uptime and future planning. TrueCommand also identifies and pinpoints errors on drives or vdevs (RAID groups), saving you valuable time when resolving issues.
>
> -- https://www.truenas.com/truecommand/

:::caution HTTPS required
This setup assumes you will be using HTTPS as TrueCommand generates ACS and Redirect URLs based on the complete URL.
:::

## Preparation

The following placeholders are used in this guide:

- `truecommand.company` is the FQDN of the TrueCommand installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of TrueCommand with authentik, you need to create an application/provider pair in authentik.

### Create property mappings

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**. Create three or five **SAML Provider Property Mapping**s, depending on your setup, with the following settings:
    - **Username Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `unique_name`
        - **Friendly Name**: Leave blank
        - **Expression**: `return request.user.username`
    - **Email Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `email`
        - **Friendly Name**: Leave blank
        - **Expression**: `return request.user.email`
    - **Name Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `given_name` or `display_name`
        - **Friendly Name**: Leave blank
        - **Expression**: `return request.user.name`
    - **Title Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `title`
        - **Friendly Name**: Leave blank
        - **Expression**: `return [custom_attribute]`
    - **Telephone Number Mapping:**
        - **Name**: Choose a descriptive name
        - **SAML Attribute Name**: `telephone_number`
        - **Friendly Name**: Leave blank
        - **Expression**: `return [custom_attribute]`

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://truecommand.company/saml/acs`.
        - Set the **SLS URL** to `https://truecommand.company/saml/slo`.
        - Set the **SLS Binding** to `Post`.
        - Set the **Logout Method** to `Front-channel (Iframe)`.
        - Under **Advanced protocol settings**, add the three or five **Property mappings** you created in the previous section, set the **NameID Property Mapping** to a property mapping based on the user's email, and select an available **Signing certificate**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

4. Navigate to **Applications** > **Providers** > **_Provider_**, then click **Copy download URL** to save the **metadata URL** to your clipboard.

## TrueCommand configuration

1. Click the gear icon in the upper-right corner.
2. Select **Administration**.
3. Click **Configure**.
4. Set **SAML Identity Provider URL** to the metadata URL from your clipboard.
5. Click **Save**.
6. Click **Configure** again, select **Start the SAML service**, and then click **Save** to start the service.

## Configuration verification

To verify that authentik is correctly integrated with TrueCommand, log out of TrueCommand and sign back in with SAML. After authenticating with authentik, you should be redirected back to TrueCommand.

## Resources

- [TrueNAS Docs - SAML](https://www.truenas.com/docs/truecommand/administration/settings/samlad/)
