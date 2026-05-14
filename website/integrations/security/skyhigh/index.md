---
title: Integrate with Skyhigh Security
sidebar_label: Skyhigh Security
support_level: community
---

## What is Skyhigh Security?

> Skyhigh Security is a Security Services Edge (SSE), Cloud Access Security Broker (CASB), and Secure Web Gateway (SWG), and Private Access (PA / ZTNA) cloud provider.
>
> -- https://www.skyhighsecurity.com/en-us/about.html

## Multiple integration points

Skyhigh has multiple points for SAML integration:

- Dashboard administrator login - allows you to manage the Skyhigh Security dashboard
- Web Gateway and Private Access - Authenticates for Internet access and ZTNA/Private Access

The following placeholder will be used throughout this document.

- `authentik.company` is the FQDN of the authentik installation.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## Integration for dashboard administrator login

### Configure Skyhigh Security

While logged in to your Skyhigh Security Dashboard, click the configuration gear and navigate to the **User Management > SAML Configuration > Skyhigh Cloud Users** tab.

Under the `Identity Provider` section enter the following values:

- Issuer: `https://authentik.company/application/saml/<application_slug>/metadata/`
- Certificate: Upload the signing certificate you will use for the authentik provider
- Login URL: `https://authentik.company/application/saml/<application_slug>/sso/binding/init/`
- SP-Initiated Request Binding: HTTP-POST
- User exclusions: Select at least one administrator account to log in directly (in case something goes wrong with SAML)

Click **Save**.

Note the Audience and ACS URLs that appear. You will use these to configure authentik below.

### Configure authentik

In the authentik admin interface, navigate to **Applications > Providers**. Create a SAML provider with the following parameters:

- ACS URL: Enter the ACS URL provided by the Skyhigh Dashboard above
- Service Provider Binding: `Post`
- Audience: Enter the Audience URL provided by the Skyhigh Dashboard above
- Signing certificate: Select the certificate you uploaded to Skyhigh above
- Property mappings: Select all default mappings.
- NameID Property Mapping: `authentik default SAML Mapping: Email`

Create an application linked to this new provider and use the slug name you used in the Skyhigh section above.

## Integration for Web Gateway and Private Access

### Configure authentik

In the authentik admin interface, navigate to **Applications > Providers**. Create a SAML provider with the following parameters:

- ACS URL: `https://login.auth.ui.trellix.com/sso/saml2`
- Service Provider Binding: `Post`
- Audience: `https://login.auth.ui.trellix.com/sso/saml2`
- Signing certificate: Select any certificate
- Property mappings: Select all default mappings.

Create an application linked to this new provider and note the name of its slug.

### Configure Skyhigh Security

While logged in to your Skyhigh Security Dashboard, click the configuration gear and navigate to **Infrastructure > Web Gateway Setup**.

Under the **Setup SAML** section, click the **New SAML** button.

Configure your SAML provider as follows:

- SAML Configuration Name: Enter a descriptive name here
- Service Provider Entity ID: `https://login.auth.ui.trellix.com/sso/saml2`
- SAML Identity Provider URL: `https://authentik.company/application/saml/<application_slug>/sso/binding/post/`
- Identity Provider Entity ID: `https://authentik.company/application/saml/<application_slug>/metadata/`
- User ID Attribute in SAML Response: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
- Group ID Attribute in SAML Response: `http://schemas.xmlsoap.org/claims/Group`
- Identity Provider Certificate: Upload the certificate you selected in the authentik SAML provider you created earlier
- Domain(s): Enter the email domain(s) you wish to redirect for authentication to authentik

Save your changes and publish the web policy.

:::info
You must also ensure that your web and/or private access policies grant access to users who will be authenticated. This configuration is out of scope for this document.
:::
