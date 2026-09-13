---
title: Integrate with GLPI
sidebar_label: GLPI
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is GLPI?

> GLPI is a free and open-source IT asset management and service desk application. It helps organizations manage hardware, software, tickets, users, and IT services in one central system.
>
> -- https://www.glpi-project.org

## Preparation

The following placeholders are used in this guide:

- `glpi.company` is the FQDN of the GLPI installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

This guide uses the community [samlSSO](https://github.com/DonutsNL/samlsso) plugin for GLPI 11 and later. For GLPI 10, use the older `glpisaml` release series from the same project.

### Install the samlSSO plugin

1. Log in to GLPI as an administrator.
2. Navigate to **Setup** > **Plugins** and install the **samlSSO** plugin from the GLPI Marketplace.
3. Enable the plugin.

If the plugin is not available from the Marketplace in your installation, download a compatible release from the [samlSSO GitHub releases](https://github.com/DonutsNL/samlsso/releases), extract it to `<GLPI_ROOT>/plugins/samlsso`, then install and enable it from **Setup** > **Plugins**.

### Create a SAML application in GLPI

Create the GLPI-side SAML configuration first so that you can copy the generated service provider endpoints into authentik.

1. Navigate to **Setup** > **samlSSO**.
2. Click **Add** and configure the following settings:
    - On the **General** tab:
        - **Friendly name**: `authentik`
        - **Is active**: enabled
    - On the **Security** tab:
        - **Strict**: enabled
        - **JIT user creation**: enabled

3. Click **Save**.
4. Open the `authentik` samlSSO configuration, navigate to the **Service Provider** tab, and note the **AcsUrl** and **SloUrl** values.

## authentik configuration

To support the integration of GLPI with authentik, you need to create property mappings and an application/provider pair in authentik.

### Create property mappings

GLPI uses the SAML `givenname` and `surname` claims when creating users through JIT provisioning.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings**, click **Create**, select **SAML Provider Property Mappings**, and click **Next**.
3. Configure the first mapping for the user's given name:
    - **Name**: `givenname`
    - **SAML Attribute Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname`
    - **Expression**:

        ```python
        return request.user.name.split(" ", 1)[0]
        ```

4. Click **Finish**.
5. Repeat the process to create a mapping for the user's surname:
    - **Name**: `surname`
    - **SAML Attribute Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname`
    - **Expression**:

        ```python
        return request.user.name.split(" ", 1)[-1]
        ```

6. Click **Finish**.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to create an application and provider pair. Alternatively, you can first create a provider separately, then create the application and connect it with the provider.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name, the authorization flow to use for this provider, and the following required configurations:
        - **ACS URL**: the **AcsUrl** value from GLPI.
        - **SLS URL**: the **SloUrl** value from GLPI.
        - Under **Advanced protocol settings**, select any available **Signing Certificate**.
        - Under **Advanced protocol settings**, set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
        - Under **Advanced protocol settings**, add the `givenname` and `surname` property mappings that you created earlier. Leave the managed email property mapping selected.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate

1. Navigate to **Applications** > **Providers** and click the provider that you created.
2. Under **Related objects** > **Download signing certificate**, click **Download**.

The downloaded file is required when configuring the identity provider settings in GLPI.

## GLPI configuration

### Configure the identity provider

1. Log in to GLPI as an administrator and navigate to **Setup** > **samlSSO**.
2. Click the `authentik` samlSSO configuration.
3. On the **Identity Provider** tab, configure the following settings:
    - **Entity ID**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **SSO URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **SLO URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **X509 certificate**: paste the contents of the signing certificate file that you downloaded from authentik.

4. Click **Save**.

### Configure JIT import rules _(optional)_

You can use JIT import rules to assign GLPI profiles, groups, and entities when samlSSO creates a user.

1. Navigate to **Setup** > **samlSSO** > **JIT import rules** and click **Add**.
2. Provide a **Name**, select a **Logical operator**, set **Active** to **Yes**, and click **Add**.
3. On the **Criteria** tab, create criteria that match the users that should receive the rule's actions.
4. On the **Actions** tab, create the actions that GLPI applies to matching users.
    - To grant access to child entities, add an action that sets `recursive` to `yes`.

5. Return to the **Rule** tab and click **Save**.

## Configuration verification

To confirm that authentik is properly configured with GLPI, log out of GLPI and click the **authentik** login button on the right side. After you authenticate with authentik, GLPI signs you in.

## Resources

- [samlSSO plugin repository](https://github.com/DonutsNL/samlsso)
- [GLPI Help Center - Plugins](https://help.glpi-project.org/documentation/modules/configuration/plugins)
- [GLPI Help Center - SAML plugin](https://help.glpi-project.org/doc-plugins/plugins-glpi/saml)
