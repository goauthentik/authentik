---
title: OnlyOffice
---

## What is OnlyOffice

From https://en.wikipedia.org/wiki/OnlyOffice

:::note
OnlyOffice, stylized as ONLYOFFICE, is a free software office suite developed by Ascensio System SIA, a company headquartered in Riga, Latvia. It features online document editors, platform for document management, corporate communication, mail and project management tools
:::

:::note
This is based on authentik 2021.10.4 and OnlyOffice 11.5.4.1582. Instructions may differ between versions.
:::

## Preparation

The following placeholders will be used:

- `authentik.company` is the FQDN of authentik.
- `onlyoffice.company` is the FQDN of the OnlyOffice instance.

Open your OnlyOffice instance, navigate to the settings by clicking the cog-icon in the navbar, then click on *Control Panel* on the sidebar.

In the new tab, click on *SSO* in the sidebar.

Click the *Enable Single Sign-on Authentication* checkbox to enable SSO.

Scroll down to *ONLYOFFICE SP Metadata*, and copy the *SP Entity ID (link to metadata XML)* URL. Open this URL in a new tab, and download the XML file.

## authentik Setup

Create an application in authentik, and create a SAML Provider by using *SAML Provider from Metadata*. Give the provider a name, and upload the XML file you've downloaded in the previous step.

Edit the resulting Provider, and ensure *Signing Certificate* is set to any certificate.

Navigate on the *Metadata* tab on the Provider page, and click *Copy download URL*.

## OnlyOffice Setup

Navigate back to your OnlyOffice Control panel, and paste the URL into *Load metadata from XML to fill the required fields automatically*, and click the upload button next to the input field.

Under *Attribute Mapping*, set the following values

- *First Name*: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
- *Last Name*: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
- *Email*: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`

Click save and a new SSO button will appear on the OnlyOffice login page.
