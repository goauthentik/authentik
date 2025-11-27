---
title: Integrate with Placetel
sidebar_label: Placetel
support_level: community
---

## What is Plactel

> Placetel is a German cloud communications provider, specializing in VoIP-based telephony, unified communications (UCaaS), and collaboration tools for businesses.
>
> -- https://www.placetel.de/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `company.tld` is the domain of your users' email addresses

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Placetel with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** value as it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://accounts.webex.placetel.de/users/saml/auth`.
        - Set the **Entity ID** to `authentik`.
        - Set the **SLS URL** to `https://accounts.webex.placetel.de/users/saml/idp_sign_out`.
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**, set an available **Signing Certificate** and ensure that **Sign assertions** and **Sign responses** are toggled.
        - Ensure that **Encryption Certificate** is empty.
        - Remove all **Property Mappings** except for `authentik default SAML Mapping: Email`.
        - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download metadata file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section.
3. Under **Related objects** > **Metadata**, click on **Download**. This downloaded file is your **SAML Metadata** file and it will be required in the next section.

## Placetel configuration

To integrate Plactel with authentik, you will need to setup SSO in the Placetel portal.

1. Log in to the [Placetel portal](https://accounts.placetel.com) as an Administrator.
2. Click the **Organization Name** in the bottom left corner, and select **Settings**
3. Scroll to the bottom of the page. Then, next to the **Single Sign On (SSO/SAML)** section heading, select **Edit**.
4. Import the **SAML Metadata** file that you downloaded from authentik.
5. Enter the following values:
    - **SP Entity ID**: `https://web.placetel.de`
    - **IDP Entity ID**: `authentik.company`
    - **Domains**: `company.tld`
6. Ensure that **Activate Single Sign On** is unchecked for now.
7. Click **Save settings**.

## Configuration verification

To confirm that authentik is properly configured with Plactel, log out and log back in using this link (with the appropriate Entity ID): `https://accounts.webex.placetel.de/users/saml/sign_in?entity_id=<authentik.company>`

You should be redirected to authentik and once authenticated, logged in to Placetel.

After confirming that your configuration is correct, return to the Placetel configuration page, check the **Activate Single Sign On** checkbox, and click **Save settings**.

You can now login to the Placetel portal using `accounts.webex.placetel.de`. The default login link on their homepage will not work.

## Resources

- [Placetel Help - SSO (SAML)](https://www.placetel.de/hilfe/webex-fuer-placetel/sso-saml-webex-fuer-placetel)
- [Placetel SAML Metadata](https://accounts.webex.placetel.de/users/saml/metadata)
