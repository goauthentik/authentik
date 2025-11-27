---
title: Integrate with GLPI
sidebar_label: GLPI
support_level: community
---

## What is GLPI

> GLPI (Gestionnaire Libre de Parc Informatique) is an open-source IT asset management and service desk software. It helps organizations manage hardware, software, tickets, users, and IT services in a centralized platform.
>
> -- https://www.glpi-project.org

## Preparation

The following placeholders are used in this guide:

- `glpi.company` is the FQDN of the GLPI installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## GLPI samlSSO plugin configuration

By default, GLPI only offers OAuth to subscribers. This guide instead describes how to integrate authentik with GLPI via SAML using a community plugin named [samlSSO](https://github.com/DonutsNL/samlsso) by [DonutsNL](https://github.com/DonutsNL).

### Install the samlSSO plugin

1. Download latest release from the [samlSSO GitHub project](https://github.com/DonutsNL/samlsso).
2. Unpack the release ZIP file in the `glpi/data/marketplace` directory of your GLPI installation.
3. Log in to GLPI as an administrator and navigate to **Setup** > **Plugins**.
4. Click the install icon (folder with a + symbol) next to the **samlSSO** plugin.
5. In the pop-up window that opens, click **enable**.

### Add a samlSSO instance

Now you'll need to add a samlSSO instance.

1. Navigate to **Setup** > **samlSSO**.
2. Click the **Add** button and configure the following required settings:
    - On the **General** tab:
        - **Friendly name**: `authentik`
        - **Is active**: toggled on
    - On the **Security** tab:
        - **Strict**: toggled on
        - **JIT user creation**: toggled on

3. Open the **Service Provider** tab and take note of the **Entity ID**, **AcsUrl** and **sloURL**. These values will be required in the next section.
4. Click **Save**.

## authentik configuration

To support the integration of GLPI with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **Slug** value as it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to the **AcsURL** value from GLPI.
        - Set the **Issuer** to the **Entity ID** value from GLPI.
        - Set the **Service Provider Binding** to `Post`.
        - Set the **SLS URL** to the **sloURL** value from GLPI.
        - Under **Advanced protocol settings**:
            - Select any available **Signing Certificate** and enable **Sign assertions**.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download certificate file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section (e.g. `Provider for GLPI`).
3. Under **Related objects** > **Download signing certificate**, click on **Download**. This downloaded file is your certificate file and it will be required in the next section.

## GLPI configuration

1. Log in to GLPI as an administrator and navigate to **Setup** > **samlSSO**.
2. Click on the **authentik** samlSSO instance and configure the following settings:
    - On the **Identity Provider** tab:
        - Set the **Entity ID** to same value shown for **Entity ID** on the **Service Provider** tab but without the trailing `/`.
        - Set the **SSO URL** to `https://authentik.company/application/saml/<applicaton_slug>/sso/binding/redirect/`.
        - Set the **SLO URL** to `https://authentik.company/application/saml/<application_slug>/slo/binding/redirect/`.
        - Set **X509 certificate** to the contents of the certificate file that you downloaded from authentik.

3. Click **Save** to apply the changes.

### JIT rules _(optional)_

It's possible to auto assign profiles and groups when a user is created in GLPI.

1. Log in to GLPI as an administrator, navigate to **Setup** > **samlSSO** > **JIT import rules**, and click **Add**
2. Provide a **Name**, **Logical operator** type, set **Active** to `Yes`, and then click **Add**.
3. Configure the following settings:
    - On the **Criteria** tab create creiterion to match against users.
    - On the **Actions** tab exists create actions to perform on matches users.
        - You may want to add `recursive=yes` as an action, so that matched users have access to all entities.
4. Once finished, return to the **Rule** tab and click **Save**.

## Configuration verification

To confirm that authentik is properly configured with GLPI, log out and click the new button on the right side. You will be redirected to authentik and once authenticated, you will be signed in to GLPI.

## Resources

- [samlSSO plugin documentation](https://glpi-plugins.readthedocs.io/en/latest/saml/requirements.html)
- [samlSSO plugin wiki](https://github.com/DonutsNL/samlsso/wiki)
