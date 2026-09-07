---
title: Integrate with OnlyOffice
sidebar_label: OnlyOffice
support_level: community
---

## What is ONLYOFFICE?

> ONLYOFFICE is an online office and productivity suite for document editing and collaboration. ONLYOFFICE Workspace adds document management, projects, CRM, mail, calendars, and an administrative control panel.
>
> -- https://www.onlyoffice.com/

## Preparation

The following placeholders are used in this guide:

- `onlyoffice.company` is the FQDN of the ONLYOFFICE Workspace installation.
- `authentik.company` is the FQDN of the authentik installation.

This guide is for ONLYOFFICE Workspace server installations that include the ONLYOFFICE Control Panel. ONLYOFFICE can only be connected to one SAML identity provider at a time.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

### Download the ONLYOFFICE service provider metadata

1. Log in to ONLYOFFICE Workspace as an administrator.
2. Click the cog icon in the navigation bar, then click **Control Panel** in the sidebar.
3. In the Control Panel tab, click **SSO** in the sidebar.
4. Enable **Single Sign-on Authentication**.
5. Scroll down to **ONLYOFFICE SP Metadata**.
6. Click **Download SP Metadata XML** to save the ONLYOFFICE SP metadata XML file. You will upload this file to authentik in the next section.

## authentik configuration

To support the integration of ONLYOFFICE Workspace with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider from Metadata** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configuration:
        - **Metadata**: select the SP metadata XML you downloaded from ONLYOFFICE Workspace during the preparation step.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.
3. Click **Submit** to save the new application and provider.
4. Navigate to **Applications** > **Providers** and click the provider you created.
5. Click **Edit** and set the following values:
    - Confirm that the **SLS URL** and **SLS Binding** were imported from the ONLYOFFICE SP metadata, then set **Logout Method** to `Front-channel (Iframe)`.
    - Under **Advanced protocol settings**:
        - **Signing Certificate**: select any available certificate.
        - **Sign responses**: enable this option.
6. Click **Update**.
7. Under **Related objects** > **Metadata**, click **Copy download URL**. This metadata download URL will be required in the next section.

## OnlyOffice configuration

1. Return to the ONLYOFFICE Control Panel and open **SSO**.
2. Paste the metadata download URL from authentik into **URL to IdP Metadata XML** and click the upload button next to the field.
3. Confirm that **IdP Single Logout Endpoint URL** is populated from the uploaded authentik metadata, and select the **Binding** that matches the **SLS Binding** shown on the authentik provider.
4. Under **Attribute Mapping**, set the following values:
    - **First Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
    - **Last Name**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
    - **Email**: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
5. Click **Save**.

## Configuration verification

To confirm that authentik is properly configured with ONLYOFFICE Workspace, log out of ONLYOFFICE Workspace, open it again, and click **Single Sign-on** on the login page. You should be redirected to authentik to log in, then redirected back to ONLYOFFICE Workspace.

## Resources

- [ONLYOFFICE DocSpace - Configuring ONLYOFFICE SP and Authentik IdP](https://helpcenter.onlyoffice.com/docspace/configuration/configure-authentik.aspx)
- [ONLYOFFICE Workspace - Single Sign-on overview for server version](https://helpcenter.onlyoffice.com/workspace/administration/control-panel-sso-description.aspx)
