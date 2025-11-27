---
title: Integrate with Placetel
sidebar_label: Placetel
support_level: community
---

## What is Plactel

> Placetel is a German cloud-communications provider offering businesses a virtual phone system and unified communications platform (VoIP, video-conferencing, chat, etc.).
>
> -- https://www.placetel.de/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `company.tld` is the domain of your users’ email addresses

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of Placetel with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)

- **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
- **Choose a Provider type**: select **SAML Provider** as the provider type.
- **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
    - Take note of the **slug** value as it will be required later.
    - Set the **ACS URL** to `https://accounts.webex.placetel.de/users/saml/auth`.
    - Set the **Entity ID** to any descriptive name, e.g. `authentik.company`.
    - Set the **SLS URL** to `https://accounts.webex.placetel.de/users/saml/idp_sign_out`
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, set an available signing key and make sure **Sign assertions**, as well as **Sign responses** is toggled.
    - Make sure **no encryption certificate** is selected.
    - Then, also under **Advanced protocol settings**, make sure **NameID Property Mapping** is set to `authentik default SAML Mapping: Email`.
    - Remove all other **Property Mappings**
- **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

4. Select the provider you have just created. Under **Related objects**, download the **Metadata**.

## Placetel configuration

1. To integrate Plactel with authentik, log in as an _Administrator_, click the **Organation Name** in the bottom left corner, and select **Settings** from the menu.
2. Scroll to the bottom of the page. Next to the section heading **Single Sign On (SSO/SAML)** select **Edit**.
3. Import the **Metadata** you just downloaded from authentik.
4. Fill out the form with the missing values:
    - **SP Entity ID**: `https://web.placetel.de`
    - **IDP Entity ID**: `authentik.company`
    - **Domains**: `company.tld`
5. Make sure **Activate Single Sign On** is unchecked for now.
6. Select **Save settings**.

## Configuration verification

To confirm that authentik is properly configured with Plactel, log out and log back in via authentik using `https://accounts.webex.placetel.de/users/saml/sign_in?entity_id=authentik.company`.

Once you're sure your configuration is correct, go back to the Placetel configuration, select the **Activate Single Sign On** checkbox and hit **Save settings**. 

You can now login to the Placetel portal using `accounts.webex.placetel.de` (the default login-link on their homepage will not work).

## Resources

- [Placetel SSO Configuration Documentation](https://www.placetel.de/hilfe/webex-fuer-placetel/sso-saml-webex-fuer-placetel)
- [Placetel SAML Metadata](https://accounts.webex.placetel.de/users/saml/metadata)
