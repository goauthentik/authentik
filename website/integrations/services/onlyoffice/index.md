---
title: OnlyOffice
---

<span class="badge badge--secondary">Support level: Community</span>

## What is OnlyOffice

> OnlyOffice, stylized as ONLYOFFICE, is a free software office suite developed by Ascensio System SIA, a company headquartered in Riga, Latvia. It features online document editors, platform for document management, corporate communication, mail and project management tools
>
> -- https://en.wikipedia.org/wiki/OnlyOffice

:::note
This is based on authentik 2021.10.4 and OnlyOffice 11.5.4.1582. Instructions may differ between versions.
:::

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of authentik.
-   `onlyoffice.company` is the FQDN of the OnlyOffice instance.

Open your OnlyOffice instance, navigate to the settings by clicking the cog-icon in the navbar, then click on _Control Panel_ on the sidebar.

In the new tab, click on _SSO_ in the sidebar.

Click the _Enable Single Sign-on Authentication_ checkbox to enable SSO.

Scroll down to _ONLYOFFICE SP Metadata_, and copy the _SP Entity ID (link to metadata XML)_ URL. Open this URL in a new tab, and download the XML file.

## authentik Setup

Create an application in authentik, and create a SAML Provider by using _SAML Provider from Metadata_. Give the provider a name, and upload the XML file you've downloaded in the previous step.

Edit the resulting Provider, and ensure _Signing Certificate_ is set to any certificate.

Navigate on the _Metadata_ tab on the Provider page, and click _Copy download URL_.

## OnlyOffice Setup

Navigate back to your OnlyOffice Control panel, and paste the URL into _Load metadata from XML to fill the required fields automatically_, and click the upload button next to the input field.

Under _Attribute Mapping_, set the following values

-   _First Name_: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
-   _Last Name_: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`
-   _Email_: `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`

Click save and a new SSO button will appear on the OnlyOffice login page.
