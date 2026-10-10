---
title: Integrate with Zoom
sidebar_label: Zoom
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is Zoom?

> Zoom is a video conferencing and collaboration platform. It allows users to hold online meetings, webinars, chats, and calls over the internet.
>
> -- https://zoom.com/

## Preparation

The following placeholders are used in this guide:

- `company.zoom.us` is the FQDN of your Zoom vanity URL. For US Government tenants, use `agency.zoomgov.com`.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

To configure SSO in Zoom, you need a Zoom Business, Education, or Enterprise account with an approved vanity URL.

## authentik configuration

To support the integration of Zoom with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Note the application **Slug** because you use it later as `<application_slug>`.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set the **ACS URL** to `https://company.zoom.us/saml/SSO`.
        - Set the **SLS URL** to `https://company.zoom.us/saml/SingleLogout`.
        - Set the **SLS Binding** to `Redirect`.
        - Set the **Logout Method** to `Front-channel (Native)`.
        - Set the **Audience** to `company.zoom.us`.
        - Under **Advanced protocol settings**, select an available **Signing Certificate**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the provider that you created in the previous section.
3. Under **Related objects** > **Download signing certificate**, click **Download** to save the certificate to your machine.
4. Open the downloaded certificate file in plain text, remove the first and last lines (`-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----`), then take note of the remaining text.

## Zoom configuration

:::info Vanity URL required
You must configure and receive approval for a Zoom vanity URL before you can use SAML SSO. Domain verification and vanity URL approval are outside the scope of this guide.
:::

:::info Support for multi-vanity configurations
This documentation covers a single Zoom vanity URL. Multiple vanity URLs or multiple IdPs require a different SP entity ID format and should be coordinated with Zoom Support.
:::

1. Log in to the [Zoom web portal](https://success.zoom.us/profile) as an administrator.
2. In the navigation menu, under **Admin**, click **Advanced**, then **Single Sign-On**.
3. Select the vanity URL that you want to configure with SAML SSO. If you only have one vanity URL, additional options are not shown.
4. Configure the following required settings:
    - **Sign-in page URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **Sign-out page URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **Identity Provider Certificate**: paste the certificate contents that you noted in the previous section.
    - **Service Provider (SP) Entity ID**: `company.zoom.us`
    - **Issuer (IDP Entity ID)**: `https://authentik.company/application/saml/<application_slug>/metadata/`
    - **Binding**: `HTTP-POST`
    - **Signature Hash Algorithm**: `SHA-256`
    - **Security options**: select **Sign SAML request**.
    - **Provision User**: select **At Sign-In**.
5. Click **Save Changes**.

## Configuration verification

To confirm that authentik is properly configured with Zoom, open Zoom and select **Sign in**. You should be redirected to authentik for authentication and then redirected back to Zoom.

## Resources

- [Zoom Support - Quick start guide for single sign-on](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0060673)
- [Zoom Support - Guidelines for Vanity URL requests](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0061540)
