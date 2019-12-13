# Rancher Integration

Rancher can authenticate against passbook using SAML.

## Preparation

The following placeholders will be used:

-   `rancher.company` is the FQDN of the Rancher Install
-   `passbook.company` is the FQDN of the passbook Install

Create an application in passbook and note the slug, as this will be used later. Create a SAML Provider with the following Parameters:

-   `ACS URL`: https://rancher.company/v1-saml/adfs/saml/acs
-   `Audience`: https://rancher.company/v1-saml/adfs/saml/metadata
-   `Issuer`: passbook

You can of course use a custom Signing Certificate, and adjust the Assertion Length.

## Rancher

![aaa](./rancher.png)
