---
title: Integrate with KnowBe4
sidebar_label: KnowBe4
support_level: community
---

## What is KnowBe4

> KnowBe4 is a security awareness and phishing simulation platform that helps organizations train employees to recognize and respond to social engineering attacks.
>
> -- https://knowbe4.com/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of KnowBe4 with authentik, you need to create an application/provider pair in authentik.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair. (Alternatively you can first create a provider separately, then create the application and connect it with the provider.)
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Temporarily set the **ACS URL** to `https://temp.temp`
        - Set the **Service Provider Binding** to `Post`.
        - Under **Advanced protocol settings**, select any available signing certificate.
    - **Configure Bindings** _(optional)_: create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to control which users see the KnowBe4 application on the **My Applications** page.

3. Click **Submit**.

### Get certificate fingerprint

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **System** > **Certificates** and expand the certificate that you selected in the previous section.
3. Take note of the **Certificate Fingerprint (SHA256)**. This value will be required in the next section.

## KnowBe4 configuration

1. Log in to the [KnowBe4 Admin Console](https://eu.knowbe4.com/ui/login).
2. Navigate to **Account Integrations** > **SAML**.
3. Set the following required configurations:
    - **Enable SAML SSO**
    - **Disable non-SAML Logins for All Users**
    - **Allow Admins w/MFA to Bypass SAML Login**
    - **Allow Account Creation from SAML Login**
    - **IdP SSO Target URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/redirect/`
    - **IdP Cert Fingerprint**: Set to the SHA-256 thumbprint of the authentik signing certificate.
4. Take note of the **Entity ID** and **SSO Callback (ACS) URL**. They will be required in the next section.

:::info SSO Misconfiguration
If SSO misconfiguration locks you out and you enabled **Allow Admins w/MFA to Bypass SAML Login**, use the **Bypass-SSO Login URL** displayed in KnowBe4 to authenticate with your credentials and fix or disable the SAML settings.
:::

## Reconfigure authentik provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the **Edit** icon of the newly created KnowBe4 provider.
3. Update the following fields:
    - Set the **ACS URL** to the **SSO Callback (ACS) URL** from KnowBe4.
    - Set the **Issuer** and **Audience** to the **Entity ID** from KnowBe4.
4. Click **Update**.

## Configuration verification

To confirm that authentik is properly configured with KnowBe4, log out of your current session. Next, go to the KnowBe4 login portal and enter an email address that uses SSO. You should be redirected to authentik, and upon successful login, logged in to the KnowBe4 console.

## Resources

- [KnowBe4 Knowledge Base - SAML Single Sign-On (SSO)](https://support.knowbe4.com/hc/en-us/articles/206293387-SAML-Integration-Overview)
