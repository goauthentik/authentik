---
title: Integrate with Placetel
sidebar_label: Placetel
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Placetel?

> Placetel is a German cloud communications provider, specializing in VoIP-based telephony, unified communications (UCaaS), and collaboration tools for businesses.
>
> -- https://www.placetel.de/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `company.tld` is the domain of your users' email addresses.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Placetel with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** value as it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://accounts.webex.placetel.de/users/saml/auth`.
        - Set the **SLS URL** to `https://accounts.webex.placetel.de/users/saml/idp_sign_out`.
        - Under **Advanced protocol settings**, set an available **Signing Certificate** and ensure that **Sign assertions** and **Sign responses** are enabled.
        - Remove all **Property Mappings** except for `authentik default SAML Mapping: Email`.
        - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download the metadata file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section.
3. Under **Related objects** > **Metadata**, click **Download**. This downloaded file is your **SAML Metadata** file and is required in the next section.

## Placetel configuration

To integrate Placetel with authentik, configure SSO in the Placetel portal.

1. Log in to the [Placetel portal](https://accounts.webex.placetel.de) as an Administrator.
2. Click the organization name in the bottom-left corner and select **Settings**.
3. Scroll to the bottom of the page. Next to the **Single Sign On (SSO/SAML)** section heading, select **Edit**.
4. In the **Import** section, click **Choose File** and upload the **SAML Metadata** file that you downloaded from authentik.
5. In the **Settings** section, confirm or enter the following values:
    - **SP Entity ID**: `https://web.placetel.de` with no trailing slash.
    - **IDP Entity ID**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **Domains**: `company.tld`. Add any other email domains that should use SSO.
6. Leave **Activate Single Sign On** unchecked until you are ready to switch Placetel sign-ins to SSO.
7. Click **Save settings**.

### Activate SSO

After saving the configuration, return to the Placetel SSO configuration page, check **Activate Single Sign On**, and click **Save settings**.

## Configuration verification

To confirm that authentik is properly configured with Placetel, open the Placetel portal and sign in with an existing Placetel user's email address. Placetel does not create new users through authentik. After clicking **Login**, you should be redirected to authentik and then signed in to Placetel.

:::info Login link
The default login link on the Placetel homepage will not work.
:::

## Resources

- [Placetel Help - SSO (SAML)](https://www.placetel.de/hilfe/webex-fuer-placetel/sso-saml-webex-fuer-placetel)
- [Placetel SAML Metadata](https://accounts.webex.placetel.de/users/saml/metadata)
