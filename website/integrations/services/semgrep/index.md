---
title: Semgrep
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Semgrep

> **Semgrep**: An application security solution that combines SAST, SCA, and secret detection.
> -- https://semgrep.dev

## Preparation

The following placeholders will be used:

-   `authentik.company.blah` is the FQDN of the authentik install.
-   `devcompany` is the organization name on Semgrep Cloud platform.

## authentik configuration

1. Login into authentik instance as an administrator.
2. Navigate to **Customization** -> **Property mappings**.
3. Create a new SAML property mapping with these parameters:
    - **Name**: `semgrep-name`
    - **SAML Attribute name**: `name`
    - **Expression**: `return request.user.name`
4. Create another SAML property mapping with these parameters:
    - **Name**: `semgrep-email`
    - **SAML Attribute name**: `email`
    - **Expression**: `return request.user.email`
5. Navigate to **System** -> **Certificates**.
6. Generate a new RSA certificate, pick a name.
7. Download the generated certificate, as you will need it later.
8. Create a new SAML provider under **Applications** -> **Providers** using the following settings:
    - **ACS URL**: `https://semgrep.dev/api/auth/saml/devcompany/`
    - **Issuer**: `https://authentik.company`
    - **Audience**: `semgrep-dev`
    - **Service Provider Binding**: `Post`
    - **Signing Keypair**: Select the RSA certificate you have generated previously.
    - **Property mappings**: Select `semgrep-name` and `semgrep-email` mappings, replacing authentik-provided email and name mappings.
9. Create a new application under **Applications** -> **Applications**, pick a name and a slug, and assign the provider that you have just created.

## Semgrep Configuration

1. Login to Semgrep Cloud platform as an administrator.
2. Click **Settings** on bottom left corner.
3. Navigate to **Access** -> **Login methods**.
4. Locate Single sign-on entry, click **Add SSO configuration**, select **SAML2 SSO** from the drop down.
5. Fill in the following:
    - **Display name**: Anything you like.
    - **Email domain**: `company.blah`
    - **IdP SSO URL**: `https://authentik.company.blah/application/saml/_slug_/sso/binding/post/`
    - **IdP Issuer ID**: `https://authentik.company`
    - **Upload/paste certificate**: Downloaded from the previous step.

## Verification

1. Go to `https://semgrep.dev/login` from Incognito mode.
2. Click **Use SSO** on the login screen.
3. Enter an email address that belongs to email domain you have entered earlier.
4. Authorize with authentik.
5. You will be redirected to home screen of Semgrep Cloud platform.
