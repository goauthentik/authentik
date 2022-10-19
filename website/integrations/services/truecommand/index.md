---
title: TrueCommand
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Service Name

From https://www.truenas.com/truecommand/
:::note
What is TrueCommand?
TrueCommand is a ZFS-aware solution allowing you to set custom alerts on statistics like ARC usage or pool capacity and ensuring storag
e uptime and future planning. TrueCommand also identifies and pinpoints errors on drives or vdevs (RAID groups), saving you valuable ti
me when resolving issues.
A free open source IT asset/license management system.
:::

:::warning
This setup assumes you will be using HTTPS as TrueCommand generates ACS and Redirect based on the complete URL.
:::

## Preparation

The following placeholders will be used:

-   `truecommand.company` is the FQDN of the snipe-it install.
-   `authentik.company` is the FQDN of the authentik install.

## authentik Configuration

### Step 1 - authentik config

### Step 2 - TrueCommand Setup

### Step 3 - Application

In authentik, create an application (under _Resources/Applications_) with these settings :

-   Name: TrueCommand
-   Slug: truecommand
-   Provider: TrueCommand

## Snipe-IT LDAP Sync

## authentik Property Mapping

To create a policy mapping, go to _Customisation/Property Mappings_, click `Create` then `LDAP Property Mapping`. Name is 'sn' and set 
Object field to sn:

## authentik SAML Config

### Step 1

Create another application in authentik and note the slug you choose, as this will be used later. In the Admin Interface, go to Applica
tions ->Providers. Create a SAML provider with the following parameters:

-   ACS URL: `https://truecommand.company/saml/acs`
-   Issuer: `https://truecommand.company`
-   Service Provider Binding: `Post`
-   Audience: `https://truecommand.company`
-   Signing certificate: Select any certificate you have.
-   Property mappings: Select all Managed mappings.
-   NamedID Property Mapping: authentik default SAML Mapping: Email
    :::note
    This is to match setting the username as **mail**. If you are using another field as the username, set it here.
    :::

### Step 2

After saving your new Application and Provider, go to _Applications/Providers_ and select your newly created Provider.

Either copy the information under SAML Metadata, or click the Download button under SAML Metadata

## TrueCommand SAML Config

Configure Snipe-IT SAML settings by going to settings (he gear icon), and selecting `SAML`

-   SAML enabled: **ticked**
-   SAML IdP Metadata: (paste information copied in Step 2 above -or-
-   Click `Select File`and select the file you downloaded in Step 2
-   Attribute Mapping - Username: mail
-   SAML Force Login: **ticked**
-   SAML Single Log Out: **ticked**

All other field can be left blank.

## Additional Resources
