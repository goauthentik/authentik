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
This documentation lists only the settings that you need to change from their default values. Changing settings not mentioned in this guide can prevent single sign-on from working correctly.
:::

## KnowBe4 configuration

1. Sign in to the KnowBe4 Admin Console.
2. Navigate to **Account Integrations** > **SAML**.
3. Enable the options that match your deployment requirements. A common configuration enables:
    - **Enable SAML SSO**
    - **Disable non-SAML Logins for All Users**
    - **Allow Admins w/MFA to Bypass SAML Login**
    - **Allow Account Creation from SAML Login**
4. Provide the authentik endpoints and certificate details:
    - **IdP SSO Target URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/redirect/`
    - **IdP Cert Fingerprint**: the SHA-256 thumbprint of the authentik signing certificate you will use for this integration (recorded in authentik under **System** > **Certificates**).
5. Note the read-only values displayed by KnowBe4; you will copy these into authentik:
    - **Entity ID**
    - **SSO Callback (ACS) URL**

## authentik configuration

Create a SAML application and provider in authentik using the values supplied by KnowBe4.

### Create an application and provider in authentik

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Applications** > **Applications** and click **Create with Provider** to create an application and provider pair.

- **Application**: provide a descriptive name such as `KnowBe4`, optionally assign a group, choose a policy engine mode, and configure any UI settings. Record the **slug** because it is used in the IdP URLs you entered in KnowBe4.
- **Choose a Provider type**: select **SAML Provider**.
- **Configure the Provider**:
    - Provide a name (or accept the auto-generated value) and select the authorization flow to use.
    - Set the **ACS URL** to the **SSO Callback (ACS) URL** displayed in KnowBe4.
    - Set the **Issuer** to the **Entity ID** shown in KnowBe4.
    - Set the **Audience** to the same **Entity ID** value.
    - Set the **Service Provider Binding** to `Post`.
    - Under **Advanced protocol settings**, choose any available certificate as the **Signing Certificate**, enable **Sign Assertions**. The certificate you select is the one whose SHA-256 thumbprint you entered in KnowBe4.
- **Configure Bindings** _(optional)_: create a [binding](/docs/add-secure-apps/flows-stages/bindings/) (policy, group, or user) to control which users see the KnowBe4 application on the **My Applications** page.

3. Click **Submit** to save the application and provider.

:::note
If SSO misconfiguration locks you out and you enabled **Allow Admins w/MFA to Bypass SAML Login**, use the **Bypass-SSO Login URL** displayed in KnowBe4 to authenticate with your credentials and fix or disable the SAML settings.
:::

## Configuration verification

1. Open a new browser session (or private window) and browse to `https://de.knowbe4.com/` (replace with your regional KnowBe4 portal if different).
2. Enter your business email address, and click **Next**.
3. Confirm that you are redirected to authentik for authentication. Sign in with an account permitted to access KnowBe4.
4. After successful authentication, verify that you return to the KnowBe4 console without being prompted for additional credentials.
