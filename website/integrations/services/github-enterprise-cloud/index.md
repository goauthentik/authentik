---
title: GitHub Enterprise Cloud
---

<span class="badge badge--secondary">Support level: Community</span>

## What is GitHub Enterprise Cloud

> GitHub is a complete developer platform to build, scale, and deliver secure software. Businesses use our suite of products to support the entire software development lifecycle, increasing development velocity and improving code quality.
>
> -- https://docs.github.com/en/enterprise-cloud@latest/admin/overview/about-github-for-enterprises

:::note
GitHub Enterprise Cloud EMU (Enterprise Managed Users) are not compatible with authentik. GitHub currently only permits SAML/OIDC for EMU organizations with Okta and/or Azure AD.
:::

## Preparation

The following placeholders will be used:

-   `github.com/enterprises/foo` is your GitHub organization, where `foo` is the name of your enterprise
-   `authentik.company` is the FQDN of the authentik Install

Create an application in authentik and note the slug, as this will be used later. Create a SAML provider with the following parameters:

-   ACS URL: `https://github.com/enterprises/foo/saml/consume`
-   Audience: `https://github.com/enterprises/foo`
-   Issuer: `https://github.com/enterprises/foo`
-   Binding: `Post`

Under _Advanced protocol settings_, set a certificate for _Signing Certificate_.

Once the provider is created, it is advised to download the signing certificate as you will need it later.

## GitHub Configuration

Navigate to your enterprise settings by clicking your GitHub user portrait in the top right of GitHub.com, select `Your enterprises` and click `Settings` for the enterprise you wish to configure.

In the left-hand navigation, within the `Settings` section, click `Authentication security`

On this page:

-   Select the `Require SAML authentication` checkbox.
-   In `Sign on URL`, type `https://authentik.company/application/saml/<authentik application slug>/sso/binding/redirect/`
-   For `Issuer`, type `https://github.com/enterprises/foo` or the `Audience` you set in authentik
-   For `Public certificate`, paste the _full_ signing certificate into this field.
-   Verify that the `Signature method` and `Digest method` match your SAML provider settings in authentik.

![Screenshot showing populated GitHub enterprise SAML settings](ghec_saml_settings.png)

Once these fields are populated, you can use the `Test SAML configuration` button to test the authentication flow. If the flow completes successfully, you will see a green tick next to the Test button.

Scroll down to hit the `Save` button below.
