---
title: Integrate with Zoom
sidebar_label: Zoom
support_level: community
---

## What is Zoom

> Zoom is a video conferencing and collaboration platform. It allows users to hold online meetings, webinars, chats, and calls over the internet.
>
> -- https://zoom.com/

## Preparation

The following placeholders are used in this guide:

- `company.zoom.us` is the FQDN of your Zoom instance. For US Government tenants, instead use `agency.zoomgov.com`.
- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning
Configuring SSO with Zoom requires having a Zoom Business, Education, or Enterprise account.
:::

## authentik configuration

To support the integration of Zoom with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations:
        - Set the **ACS URL** to `https://company.zoom.us/saml/SSO`.
        - Set the **Issuer** to `authentik`.
        - Set the **Service Provider Binding** to `Post`.
        - Set the **SLS URL** to `https://company.zoom.us/saml/SingleLogout`.
        - Set the **SLS Binding** to `Redirect`.
        - Set the **Logout Method** to `Front-channel (Native)`.
        - Set the **Audience** to `company.zoom.us`.
        - Under **Advanced protocol settings**, select an available **Signing Certificate**.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to manage the listing and access to applications on a user's **My applications** page.

3. Click **Submit** to save the new application and provider.

### Download the signing certificate

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the application created in the previous step.
3. Under **Download signing certificate**, click **Download** to save the certificate to your machine.
4. Open the downloaded certificate file in plain text, remove the first and last lines (`-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----`), then take note of the remaining text.

## Zoom configuration

:::warning Configuring a vanity URL
You must configure a vanity URL for your Zoom account before you can use SAML SSO. More information can be found in the [Zoom documentation](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0061540).
:::

:::info Support for multi-vanity configurations
This documentation does not cover the configuration of multiple vanity URLs. For more information, please refer to the [Zoom documentation](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0061540).
:::

1. Log in to the [Zoom web portal](https://success.zoom.us/profile) as an administrator.
2. In the navigation menu, click **Advanced**, then **Single Sign-On**.
3. Select the vanity URL you wish to configure with SAML SSO. If you only have one vanity URL, additional options will not be shown.
4. Configure the following required settings:
    - **Sign-in page URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/post/`
    - **Sign-out page URL**: `https://authentik.company/application/saml/<application_slug>/slo/binding/post/`
    - **Identity Provider Certificate**: Set the contents of the certificate downloaded in the previous step.
    - **Service Provider (SP) Entity ID**: `company.zoom.us`
    - **Issuer (IDP Entity ID)**: `company.zoom.us`
    - **Binding**: `HTTP-POST`
    - **Signature Hash Algorithm**: `SHA256`
    - **Security options**: Select `Sign SAML request`
    - **Provision User**: Select `At sign-in`
5. Click **Save changes**.

## Configuration verification

To verify that authentik is configured correctly with Zoom, navigate to your company's vanity URL and click **Sign in**. You should be redirected to authentik for authentication and then redirected back to Zoom.

## Resources

- [Zoom Support - Quick start guide for single sign-on](https://support.zoom.com/hc/en/article?id=zm_kb&sysparm_article=KB0060673)
