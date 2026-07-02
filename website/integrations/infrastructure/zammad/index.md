---
title: Integrate with Zammad
sidebar_label: Zammad
support_level: community
---

import RedirectURI20265Note from "../../\_redirect-uri-2026-5-note.mdx";
import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";
import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

## What is Zammad?

> Zammad is a web-based, open source user support and ticketing system.
>
> -- https://zammad.org/

## Preparation

The following placeholders are used in this guide:

- `zammad.company` is the FQDN of the Zammad installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

<Tabs
defaultValue="saml"
values={[
{ label: "SAML", value: "saml" },
{ label: "OIDC", value: "oidc" },
]}>
<TabItem value="saml">

## authentik configuration

To support the integration of Zammad with authentik using SAML, you need to create SAML property mappings and an application/provider pair in authentik.

### Create property mappings

Zammad requests SAML attributes named `email`, `name`, `first_name`, and `last_name`. Create custom property mappings so authentik sends those attribute names in the SAML assertion.

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Property Mappings** and click **Create**.
3. Select **SAML Provider Property Mapping** as the type and click **Next**.
4. Create a property mapping with the following values:
    - **Name**: `Zammad email`
    - **SAML Attribute Name**: `email`
    - **Expression**:

        ```python
        return request.user.email
        ```

5. Click **Finish** to save the property mapping.
6. Repeat steps 2-5 to create the following additional SAML provider property mappings:
    - **Name**: `Zammad name`
    - **SAML Attribute Name**: `name`
    - **Expression**:

        ```python
        return request.user.name or request.user.get_full_name() or request.user.username
        ```

    - **Name**: `Zammad first_name`
    - **SAML Attribute Name**: `first_name`
    - **Expression**:

        ```python
        return request.user.first_name or (request.user.name.split(" ", 1)[0] if request.user.name else request.user.username)
        ```

    - **Name**: `Zammad last_name`
    - **SAML Attribute Name**: `last_name`
    - **Expression**:

        ```python
        return request.user.last_name or (request.user.name.rsplit(" ", 1)[-1] if " " in request.user.name else "")
        ```

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://zammad.company/auth/saml/callback`.
        - Set the **Audience** to `https://zammad.company/auth/saml/metadata`.
        - Set the **SLS URL** to `https://zammad.company/auth/saml/slo`.
        - Set the **SLS Binding** to `Redirect`.
        - Set the **Logout Method** to `Front-channel (Iframe)`.
        - Under **Advanced protocol settings**:
            - Select an available **Signing Certificate**.
            - Set **NameID Property Mapping** to `Zammad email`.
            - Set **Default NameID Policy** to `Email`.
            - Add the Zammad property mappings that you created earlier to **Selected User Property Mappings**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download the certificate file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section (e.g. `Provider for zammad`).
3. Under **Related objects** > **Download signing certificate**, click on **Download**. This downloaded file is your certificate file and it will be required in the next section.

## Zammad configuration

To configure Zammad's SAML integration with authentik, log in to Zammad as an administrator. Go to **Settings** (the gear icon) and select **Security** > **Third-party Applications**.

At the top of the **Third-party Applications** page, enable **Automatic account link on initial logon** if existing Zammad users should be linked to matching authentik users during their first SSO login.

1. Activate the **Authentication via SAML** toggle.
2. Set the following fields:
    - **Display name**: authentik
    - **IDP SSO target URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **IDP single logout target URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **IDP Certificate**: paste the contents of your certificate file.
    - **Name Identifier Format**: `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`
3. Click **Submit** to save the authentication settings.

:::warning SSL verification
If Zammad cannot validate the connection to authentik when saving the SAML configuration, review the certificate trust path before temporarily disabling **SSL verification**. Disabling SSL verification accepts any presented certificate and should only be used for testing or short-term troubleshooting.
:::

## Configuration verification

To verify that authentik is correctly integrated with Zammad, log out of Zammad, open Zammad, and log in by clicking the SAML button on the login screen. The button shows the **Display name** that you configured in Zammad.

</TabItem>
<TabItem value="oidc">

## authentik configuration

<RedirectURI20265Note />

To support the integration of Zammad with authentik using OIDC, you need to create an application/provider pair in authentik.

### Create an application and provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the **Slug** value because it will be required later.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **Client type** to `Public`.
        - Note the **Client ID** value because it will be required later.
        - Add a **Redirect URI** of type `Strict` `Authorization` as `https://zammad.company/auth/openid_connect/callback`.
        - Set the **Logout URI** to `https://zammad.company/auth/openid_connect/backchannel_logout`.
        - Select a **Signing Key**.
        - Under **Advanced protocol settings**, set **Subject Mode** to **Based on the User's Email**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

## Zammad configuration

To configure Zammad's OIDC integration with authentik, log in to Zammad as an administrator. Go to **Settings** (the gear icon) and select **Security** > **Third-party Applications**.

At the top of the **Third-party Applications** page, enable **Automatic account link on initial logon** if existing Zammad users should be linked to matching authentik users during their first SSO login.

1. Activate the **Authentication via OpenID Connect** toggle.
2. Set the following fields:
    - **Display name**: authentik
    - **Identifier**: enter the Client ID from authentik.
    - **Issuer**: `https://authentik.company/application/o/<application_slug>/`
    - **PKCE**: `yes`

3. Click **Submit** to save the authentication settings.

## Configuration verification

To verify that authentik is correctly integrated with Zammad, log out of Zammad, open Zammad, and log in by clicking the OIDC button on the login screen. The button shows the **Display name** that you configured in Zammad.

</TabItem>
</Tabs>

## Resources

- [Zammad Admin Documentation - SAML](https://admin-docs.zammad.org/en/latest/settings/security/third-party/saml.html)
- [Zammad Admin Documentation - OpenID Connect](https://admin-docs.zammad.org/en/latest/settings/security/third-party/openid-connect.html)
- [Zammad Admin Documentation - Third-Party Applications](https://admin-docs.zammad.org/en/latest/settings/security/third-party.html)
