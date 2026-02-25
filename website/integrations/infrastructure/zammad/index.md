---
title: Integrate with Zammad
sidebar_label: Zammad
support_level: community
---

import TabItem from "@theme/TabItem";
import Tabs from "@theme/Tabs";

## What is Zammad

> Zammad is a web-based, open source user support/ticketing solution.
> Download and install it on your own servers. For free.
>
> -- https://zammad.org/

## Preparation

The following placeholders are used in this guide:

- `zammad.company` is the FQDN of the Zammad installation.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## Configuration methods

There are two ways to configure single sign-on for Zammad; SAML or OIDC.

<Tabs
defaultValue="saml"
values={[
{ label: "Log in with SAML", value: "saml" },
{ label: "Log in with OIDC", value: "oidc" },
]}>
<TabItem value="saml">

## authentik configuration

To support the integration of Zammad with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** as it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **ACS URL** to `https://zammad.company/auth/saml/callback`.
        - Set the **Issuer** to `https://zammad.company/auth/saml/metadata`.
        - Set the **Audience** to `https://zammad.company/auth/saml/metadata`.
        - Set the **Service Provider Binding** to `Post`.
        - Set the **SLS URL** to `https://zammad.company/auth/saml/slo`.
        - Set the **SLS Binding** to `Redirect`.
        - Set the **Logout Method** to `Front-channel (Iframe)`.
        - Under **Advanced protocol settings**, select an available **Signing certificate**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download certificate file

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click on the name of the provider that you created in the previous section (e.g. `Provider for zammad`).
3. Under **Related objects** > **Download signing certificate**, click on **Download**. This downloaded file is your certificate file and it will be required in the next section.

## Zammad configuration

To configure Zammad's integration with authentik, go to **Settings** (the gear icon) and select **Security** > **Third-party Applications**. Next, activate the **Authentication via SAML** toggle and change the following fields:

1. Set the following fields:
    - **Display name**: authentik
    - **IDP SSO target URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/redirect/`
    - **IDP single logout target URL**: `https://authentik.company/application/saml/<application_slug>/slo/binding/redirect/`
    - **IDP Certificate**: paste the contents of your certificate file.
    - **IDP certificate fingerprint**: Leave this empty.
    - **Name Identifier Format**: `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress`
    - **Automatic account link on initial logon**: Enable this to automatically create Zammad users when they sign in using authentik for the first time.
2. Click **Submit** to save the authentication settings.

:::info
The **SSL verification** can fail when Zammad tries to connect to authentik directly, while accessing authentik in your browser works perfectly fine. You may have to disable the verification in order to save the configuration. See https://github.com/zammad/zammad/issues/5225 for details.
:::

</TabItem>

<TabItem value="oidc">

## authentik configuration

To support the integration of Zammad with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **OAuth2/OpenID Connect** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Set the **Client type** to `Public`.
        - Take note of the **Client ID** and **slug** values because they will be required later.
        - Set the **Redirect URIs/Origins** to `Strict` / `https://zammad.company/auth/openid_connect/callback`.
        - Select a **Signing Key**.
        - Under **Advanced protocol settings**, set **Subject mode** to **Based on the User's Email**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

## Zammad configuration

To configure Zammad's integration with authentik, go to **Settings** (the gear icon) and select **Security** > **Third-party Applications**. Next, activate the **Authentication via OpenID Connect** toggle and change the following fields:

1. Set the following fields:
    - **Display name**: authentik
    - **Identifier**: the **Client ID** from above.
    - **Issuer**: `https://authentik.company/application/o/<application_slug>/`
    - **PKCE**: set to **yes**.

2. Click **Submit** to save the authentication settings.

At the very top of the **Third-party Applications** page are a few additional settings:

- **Automatic account link on initial logon**: Enable this to automatically link existing Zammad users when they sign in using authentik for the first time.

</TabItem>
</Tabs>

## Configuration verification

To verify that authentik is correctly integrated with Zammad, log out of Zammad and then log back in by clicking the SAML or OIDC button on the login screen. The button will show the **Display Name** you specified above. You should be redirected to authentik to log in, and if the process is successful, you'll be logged in to the Zammad dashboard.

## Resources

- [Zammad Admin Documentation - SAML](https://admin-docs.zammad.org/en/latest/settings/security/third-party/saml.html)
- [Zammad Admin Documentation - OpenID Connect](https://admin-docs.zammad.org/en/latest/settings/security/third-party/openid-connect.html)
