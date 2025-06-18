---
title: Integrate with Semgrep
sidebar_label: Semgrep
support_level: community
---

## What is Semgrep

> **Semgrep**: An application security solution that combines SAST, SCA, and secret detection.
>
> -- https://semgrep.dev

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik installation.
- `devcompany` is the organization name on Semgrep Cloud platform.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

1. Log in to your authentik instance as an administrator.
2. Go to the admin interface.
3. Navigate to **Customization** -> **Property mappings**.
4. Create a new SAML property mapping with these parameters:
    - **Name**: `semgrep-name`
    - **SAML Attribute name**: `name`
    - **Expression**: `return request.user.name`
5. Create another SAML property mapping with these parameters:
    - **Name**: `semgrep-email`
    - **SAML Attribute name**: `email`
    - **Expression**: `return request.user.email`
6. Navigate to **System** -> **Certificates**.
7. Generate a new RSA certificate.
8. Download the generated certificate, as you will need it later.
9. Create a new SAML provider under **Applications** -> **Providers** using the following settings:
    - **ACS URL**: `https://semgrep.dev/api/auth/saml/devcompany/`
    - **Issuer**: `https://authentik.company`
    - **Audience**: `semgrep-dev`
    - **Service Provider Binding**: `Post`
    - **Signing Keypair**: Choose the RSA certificate you generated earlier.
    - **Property mappings**: `semgrep-name` and `semgrep-email`
10. Create a new application under **Applications** -> **Applications**, pick a name and a slug, and assign the provider that you just created.

## Semgrep configuration

1. Log in to Semgrep Cloud platform as an administrator.
2. Click **Settings** on bottom left corner.
3. Navigate to **Access** -> **Login methods**.
4. Locate Single sign-on entry, click **Add SSO configuration**, select **SAML2 SSO** from the drop down.
5. Fill in the following:
    - **Display name**: Anything you like.
    - **Email domain**: `company`
    - **IdP SSO URL**: `https://authentik.company/application/saml/<application_slug>/sso/binding/post/`
    - **IdP Issuer ID**: `https://authentik.company`
    - **Upload/paste certificate**: Downloaded from the previous step.

## Verification

1. Open an Incognito window and navigate to `https://semgrep.dev/login`
2. Click **Use SSO** on the login screen.
3. Enter the email address associated with the domain you provided earlier.
4. Log in to authentik.
5. You will be redirected to the home screen of Semgrep Cloud platform.
