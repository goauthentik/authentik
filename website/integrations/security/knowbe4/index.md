---
title: Integrate with KnowBe4
sidebar_label: KnowBe4
support_level: community
---

import SAMLProvider20265Warning from "../../\_saml-provider-2026-5-warning.mdx";

## What is KnowBe4?

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

<SAMLProvider20265Warning />

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **New Application** to open the application wizard.
    - **Application**: provide a descriptive name, an optional group for the type of application, the policy engine mode, and optional UI settings. Take note of the **slug** value because it will be required later.
    - **Choose a Provider type**: select **SAML Provider** as the provider type.
    - **Configure the Provider**: provide a name (or accept the auto-provided name), the authorization flow to use for this provider, and the following required configurations.
        - Temporarily set the **ACS URL** to `https://temp.temp`
        - Under **Advanced protocol settings**:
            - Set the **Signing Certificate** to any available certificate.
            - Set **NameID Property Mapping** to `authentik default SAML Mapping: Email`.
            - Set **Default NameID Policy** to `Email address`.
    - **Configure Bindings** _(optional)_: you can create a [binding](/docs/add-secure-apps/bindings-overview/) (policy, group, or user) to manage the listing and access to applications on a user's **Application Dashboard** page.

3. Click **Submit** to save the new application and provider.

### Get certificate fingerprint

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **System** > **Certificates** and expand the certificate that you selected in the previous section.
3. Take note of the **Certificate Fingerprint (SHA256)**. This value will be required in the next section.

## KnowBe4 configuration

1. Log in to the KnowBe4 Security Awareness Training console as an account administrator.
2. Click your email address in the upper-right corner and select **Account Settings**.
3. Navigate to **Account Integrations** > **SAML** and expand the **SAML Settings** box.
4. Take note of the **Entity ID** and **SSO Callback (ACS) URL**. They will be required in the next section.
5. Set the following required configurations:
    - Enable **Enable SAML SSO**.
    - **IdP SSO Target URL**: `https://authentik.company/application/saml/<application_slug>/`
    - **IdP Cert Fingerprint**: select **SHA-256** and enter the **Certificate Fingerprint (SHA256)** value from authentik.
6. Review the optional SAML settings before saving:
    - Enable **Allow Account Creation from SAML Login** if you want KnowBe4 to create users the first time they sign in with SAML.
    - After you verify that SSO works, decide whether to enable **Disable non-SAML Logins for All Users**. If you enable it, decide whether to also enable **Allow Admins with MFA to Bypass SAML Login** so MFA-protected administrators can use KnowBe4's bypass URL to recover from an SSO misconfiguration.
7. Click **Save SAML Settings**.

## Reconfigure authentik provider

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Providers** and click the **Edit** icon of the KnowBe4 provider.
3. Set the following required configurations:
    - Under **Protocol settings**, set **ACS URL** to the **SSO Callback (ACS) URL** from KnowBe4.
    - Under **Protocol settings**, set **Audience** to the **Entity ID** from KnowBe4.
4. Click **Update**.

## Configuration verification

To confirm that authentik is properly configured with KnowBe4, log out of KnowBe4 and then open the KnowBe4 login page in a private or incognito browser window. Enter an email address that uses SSO and confirm that you are redirected to authentik for authentication and then back to the KnowBe4 console.

## Resources

- [KnowBe4 Knowledge Base - Set Up SAML Single Sign-on (SSO) for the Security Awareness Training Console](https://support.knowbe4.com/hc/en-us/articles/360041935913-Set-Up-SAML-Single-Sign-on-SSO-for-the-Security-Awareness-Training-Console)
- [KnowBe4 Knowledge Base - KnowBe4 Console Account Settings: Account Integrations](https://support.knowbe4.com/hc/en-us/articles/12769050560403-KnowBe4-Console-Account-Settings-Account-Integrations)
- [KnowBe4 Knowledge Base - SAML Integration Overview](https://support.knowbe4.com/hc/en-us/articles/206293387-SAML-Integration-Overview)
