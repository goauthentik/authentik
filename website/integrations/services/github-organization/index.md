---
title: GitHub Organization
---

<span class="badge badge--secondary">Support level: Community</span>

## What is GitHub Organizations

> Organizations are shared accounts where businesses and open-source projects can collaborate across many projects at once, with sophisticated security and administrative features.
>
> -- https://docs.github.com/en/organizations/collaborating-with-groups-in-organizations/about-organizations

## Preparation

The following placeholders will be used:

-   `github.com/orgs/foo` is your GitHub organization, where `foo` is the name of your org
-   `authentik.company` is the FQDN of the authentik Install

Create an application in authentik and note the slug, as this will be used later. Create a SAML provider with the following parameters:

-   ACS URL: `https://github.com/orgs/foo/saml/consume`
-   Audience: `https://github.com/orgs/foo`
-   Issuer: `https://github.com/orgs/foo`
-   Binding: `Post`

Under _Advanced protocol settings_, set a certificate for _Signing Certificate_.

Once the provider is created, it is advised to download the signing certificate as you will need it later.

## GitHub Configuration

Navigate to your organization settings by going to your organization page at https://github.com/foo, then click Settings.

In the left-hand navigation, scroll down to the Security section and click `Authentication security`

On this page:

-   Select the `Enable SAML authentication` checkbox.
-   In `sign-on URL`, type `https://authentik.company/application/saml/<authentik application slug>/sso/binding/redirect/`
-   For `Issuer`, type `https://github.com/orgs/foo` or the `Audience` you set in authentik
-   For `Public certificate`, paste the _full_ signing certificate into this field.
-   Verify that the `Signature method` and `Digest method` match your SAML provider settings in authentik.

Once these fields are populated, you can use the `Test SAML configuration` button to test the authentication flow. If the flow completes successfully, you will see a green tick next to the Test button.

Scroll down to hit the `Save` button below.

![Screenshot showing populated GitHub organization SAML settings](ghorg_saml_settings.png)

This enables SAML as an authentication _option_. If you want to _require_ SAML for your organization, visit your SSO url at `https://github.com/orgs/foo/sso` and sign in. Once signed in, you can navigate back to the `Authentication security` page and check `Require SAML SSO authentication for all members of the foo organization.`
