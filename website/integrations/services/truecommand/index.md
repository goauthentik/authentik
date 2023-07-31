---
title: TrueNAS TrueCommand
---

<span class="badge badge--secondary">Support level: Community</span>

## What is TrueNAS TrueCommand

> TrueCommand is a ZFS-aware solution allowing you to set custom alerts on statistics like ARC usage or pool capacity and ensuring storage uptime and future planning. TrueCommand also identifies and pinpoints errors on drives or vdevs (RAID groups), saving you valuable time when resolving issues.
>
> -- https://www.truenas.com/truecommand/

:::caution
This setup assumes you will be using HTTPS as TrueCommand generates ACS and Redirect URLs based on the complete URL.
:::

## Preparation

The following placeholders will be used:

-   `truecommand.company` is the FQDN of the snipe-it install.
-   `authentik.company` is the FQDN of the authentik install.

Create an application in authentik and use the slug for later as `truenas-truecommand`.

Create a SAML provider with the following parameters:

-   ACS URL: `https://truecommand.company/saml/acs`
-   Issuer: `truecommand-saml`
-   Binding: `Post`

Under _Advanced protocol settings_, set a certificate for _Signing Certificate_.
Under _Advanced protocol settings_, set NameID Property to _authentik default SAML Mapping: Email_.

## SAML Property Mappings

The following custom property mappings are required.

Under _Customisation_, select _Property Mappings_, then _Create_. Select _SAML Property Mapping_.

### Username

-   Name: `Truecommand - Username`
-   SAML Attribute Name: `unique_name`
-   Expression

```python
return request.user.username
```

### Email

-   Name: `Truecommand - Email`
-   SAML Attribute Name: `email`
-   Expression

```python
return request.user.email
```

### Fullname

-   Name: `Truecommand - Fullname`
-   SAML Attribute Name: `given_name` OR `display_name`
-   Expression

```python
return request.user.name
```

### Other Attributes

If you have custom attributes, or attributes imported from Active Directory, TrueCommand supports the following additional mappings:

#### Role

-   Name: `Truecommand - Role`
-   SAML Attribute Name: `title`
-   Expression

```python
return [custom_attribute]
```

#### Phone Number

-   Name: `Truecommand - Phone Number`
-   SAML Attribute Name: `telephone_number`
-   Expression

```python
return [custom_attribute]
```

Return to _Providers_ under _Applications_, and edit the Provider created above.

Under _Advanced protocol settings_, select the additional property mappings created above.

### SAML Metadata

Click the _Copy download URL_ to save the Metadata URL into your clipboard.

## TrueCommand Config

-   Click on the gear icon in the upper right corner.
-   Select Administration
-   Click on CONFIGURE
-   SAML Identity Provider URL: `Paste the Metadata URL from your clipboard.`
-   Click _Save_, then click _Configure_ again then select _Start the SAML service_, then click _Save_ to start the service.

## Additional Resources

-   https://www.truenas.com/docs/truecommand/administration/settings/samlad/
