---
title: Google Workspace
---

<span class="badge badge--primary">Support level: authentik</span>

## What is Google Workspace

From https://en.wikipedia.org/wiki/Google_Workspace

:::note
Google Workspace is a collection of cloud computing, productivity and collaboration tools, software and products developed and marketed by Google.
:::

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of the authentik install.
-   `example.com` is the default E-mail address configured in Google workspace.

## authentik Configuration

Create an application in authentik and note the slug, as this will be used later. Set the _Launch URL_ to `https://mail.google.com/a/example.com`.

Create a SAML provider with the following parameters:

-   ACS URL: `https://www.google.com/a/example.com/acs`
-   Issuer: `google.com/a/example.com`
-   Binding: `Post`
-   Audience: `google.com/a/example.com`

Under _Advanced protocol settings_, set the option _NameID Property Mapping_ to the default E-mail property mapping called _authentik default SAML Mapping: Email_. Also make sure a _Signing Certificate_ is selected in the same section.

Copy the values of _SSO URL (Redirect)_ and _SLO URL (Redirect)_ fields from the provider page.

Click the _Download_ button next to the _Download signing certificate_ label.

## Google Workspace Configuration

Log in to the Google Workspace Admin portal by navigating to https://admin.google.com/, and authenticating with a super-admin account.

Navigate to _Security_ -> _Authentication_ -> _SSO with third-party IdP_.

Open the _Third-party SSO profile for your organization_ section.

Check the checkbox _Set up SSO with third-party identity provider_.

Set the value of _Sign-in page URL_ to the copied _SSO URL (Redirect)_ from above.

Set the value of _Sign-out page URL_ to the copied _SLO URL (Redirect)_ from above.

For _Verification certificate_, upload the certificate that you downloaded previously.

Ensure the option _Use a domain specific issuer_ is enabled.

## Notes

Google will not use these SSO settings with super-admins, although they will apply for any other user account. User accounts must already exist in Google workspace when attempting to login with authentik; Google will not create them automatically.

To verify that the configuration is correct for a super-admin account, navigate to `https://mail.google.com/a/example.com`, which redirects to the configured authentik instance.
