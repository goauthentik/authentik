---
title: Snipe-IT
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Snipe-IT

From https://snipeitapp.com
:::note
A free open source IT asset/license management system.
:::

:::caution
This setup assumes you will be using HTTPS as Snipe-It dynamically generates the ACS and other settings based on the complete URL.
:::

:::caution
In case something goes wrong with the configuration, you can use the URL `http://inventory.company/login?nosaml` to log in using the
built-in authentication.
:::

## Preparation

The following placeholders will be used:

-   `inventory.company` is the FQDN of the snipe-it install.
-   `authentik.company` is the FQDN of the authentik install.
-   `snipeit-user` is the name of the authentik service account we will create.
-   `DC=ldap,DC=authentik,DC=io` is the Base DN of the LDAP Provider (default)

## authentik Configuration

### Step 1 - Service account

In authentik, create a service account (under _Directory/Users_) for Snipe-IT to use as the LDAP Binder and take note of the password generated.

In this example, we'll use `snipeit-user` as the Service account's username

:::note
If you didn't keep the password, you can copy it from _Directory/Tokens & App password_.
:::

### Step 2 - LDAP Provider

In authentik, create a LDAP Provider (under _Applications/Providers_) with these settings :

-   Name : Snipe IT-LDAP
-   Bind DN : `DC=ldap,DC=goauthentik,DC=io`
-   Certificate : `authentik Self-signed Certificate`

### Step 3 - Application

In authentik, create an application (under _Resources/Applications_) with these settings :

-   Name: Snipe IT-LDAP
-   Slug: snipe-it-ldap
-   Provider: Snipe IT-LDAP

### Step 4 - Outpost

In authentik, create an outpost (under _Applications/Outposts_) of type `LDAP` that uses the LDAP Application you created in _Step 3_.

-   Name: LDAP
-   Type: LDAP

## Snipe-IT LDAP Setup

Configure Snipe-IT LDAP settings by going to settings (he gear icon), and selecting `LDAP`

Change the following fields

-   LDAP Integration: **ticked**
-   LDAP Password Sync: **ticked**
-   Active Directory : **unticked**
-   LDAP Client-Side TLS Key: (taken from authentik)
-   LDAP Server: `ldap://authentik.company`
-   Use TLS : **unticked**
-   LDAP SSL certificate validation : **ticked**
-   Bind credentials:
    -   LDAP Bind USername: `cn=snipeit-user,ou=users,dc=ldap,dc=goauthentik,dc=io`
    -   LDAP Bind Password: `<snipeit-user password from step 2>`
-   Base Bind DN: `ou=users,DC=ldap,DC=goauthentik,DC=io`
    :::note
    ou=users is the default OU for users. If you are using authentik's virtual groups, or have your users in a different organizational unit (ou), change accordingly.
    :::
-   LDAP Filter: &(objectClass=user)
-   Username Field: mail
    :::note
    Setting the Username field to mail is recommended in order to ensure the usernameisunique. See https://snipe-it.readme.io/docs/ldap-sync-login
    :::
-   Allow unauthenticated bind: **unticked**
-   Last Name: sn
-   LDAP First Name: givenname
-   LDAP AUthentication query: cn=
-   LDAP Email: mail

:::note
authentik does not support other LDAP attributes like Employee Number, Department, etc out of the box. If you need these fields, you will need to setup custom attributes.
:::

Save your config, then click on Test LDAP Synchorization. This does not import any users, just verifies everything is working and the account can search the directory.

To test your settings, enter a username and password and click Test LDAP.

## Snipe-IT LDAP Sync

You must sync your LDAP database with Snipe-IT. Go to People on the sidebar menu.

-   CLick `LDAP Sync`
-   Select your Location
-   Click Synchronize
    :::note
    Snipe-IT will only import users with both a first and last name set. If you do not have first and last names stored in your users attributes, you can create a property mapping to set first and last name.
    :::

## authentik Property Mapping

To create a policy mapping, go to _Customisation/Property Mappings_, click `Create` then `LDAP Property Mapping`. Name is 'sn' and set Object field to sn:

```ini
def getLastName():
    if len(request.user.name) >= 1:
     return request.user.name.split(" ")[1]
    elif len(request.user.name) == 1:
     return request.user.name.split(" ")[1]
    else:
      return ""

return {
    "sn": getLastName(),
}

```

Create a second policy mapping, name it 'givenname' and set Object field to 'givenname'

```
def getFirstName():
    if len(request.user.name) >= 1:
     return request.user.name.split(" ")[0]
    else:
      return f"N/A"

return {
    "givenname": getFirstName(),
}
```

## authentik SAML Config

### Step 1

Create another application in authentik and note the slug you choose, as this will be used later. In the Admin Interface, go to Applications ->Providers. Create a SAML provider with the following parameters:

-   ACS URL: `https://inventory.company/saml/acs`
-   Issuer: `https://inventory.company`
-   Service Provider Binding: `Post`
-   Audience: `https://inventory.company`
-   Signing certificate: Select any certificate you have.
-   Property mappings: Select all Managed mappings.
-   NamedID Property Mapping: authentik default SAML Mapping: Email
    :::note
    This is to match setting the username as **mail**. If you are using another field as the username, set it here.
    :::

### Step 2

After saving your new Application and Provider, go to _Applications/Providers_ and select your newly created Provider.

Either copy the information under SAML Metadata, or click the Download button under SAML Metadata

## Snipe-IT SAML Config

Configure Snipe-IT SAML settings by going to settings (he gear icon), and selecting `SAML`

-   SAML enabled: **ticked**
-   SAML IdP Metadata: (paste information copied in Step 2 above -or-
-   Click `Select File`and select the file you downloaded in Step 2
-   Attribute Mapping - Username: mail
-   SAML Force Login: **ticked**
-   SAML Single Log Out: **ticked**

All other field can be left blank.

## Additional Resources

-   https://snipe-it.readme.io/docs/ldap-sync-login
-   https://snipe-it.readme.io/docs/saml
