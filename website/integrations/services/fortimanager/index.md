---
title: FortiManager
---

<span class="badge badge--secondary">Support level: Community</span>

## What is FortiManager

> FortiManager supports network operations use cases for centralized management, best practices compliance, and workflow automation to provide better protection against breaches.
>
> FortiManager is a paid enterprise product.
>
> -- https://www.fortinet.com/products/management/fortimanager

## Preparation

The following placeholders will be used:

-   `fgm.company` is the FQDN of the FortiManager install.
-   `authentik.company` is the FQDN of the authentik install.

Create an application and Provider in authentik, note the slug, as this will be used later. Create a SAML provider with the following parameters:

Provider:

-   ACS URL: `https://fgm.company/saml/?acs`
-   Issuer: `https://authentik.company/application/saml/fgm/sso/binding/redirect/`
-   Service Provider Binding: Post

You can of course use a custom signing certificate, and adjust durations.

Application:

-   Launch URL: 'https://fgm.company/p/sso_sp/'

## FortiManager Configuration

Navigate to `https://fgm.company/p/app/#!/sys/sso_settings` and select SAML SSO settings to configure SAML.

Select 'Service Provider (SP)' under Single Sign-On Mode to enable SAML authentication.

Set the Field 'SP Address' to the FortiManager FQDN 'fgm.company'. (This gives you the URLs to configure in authentik)

Set the Default Login Page to either 'Normal' or 'Single-Sign On'. (Normal allows both local and SAML authentication vs only SAML SSO)

FortiManager create a new user by default if one does not exist so you will need to set the Default Admin Profile to the permissions you want any new users to have. (We created a no_permissions profile to assign by default)

Set the Field 'IdP Type' to 'Custom'

Set the Field `IdP entity ID` to `https://authentik.company/application/saml/fgm/sso/binding/redirect/`.

Set the Field `IdP Login URL` to `https://authentik.company/application/saml/fgm/sso/binding/redirect/`.

Set the Field `IdP Logout URL` to `https://authentik.company/`

For the Field 'IdP Certificate" Import your authentik cert. (Self Signed or real)
