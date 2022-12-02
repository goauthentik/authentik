---
title: Calibre-Web
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Calibre-Web

From https://github.com/janeczku/calibre-web

:::note
Calibre-Web is a web app providing a clean interface for browsing, reading and downloading eBooks using a valid Calibre database.
:::

## Preparation

The following placeholder will be used:

-   `ldapservice` is the username of the authentik admin user you'd like to use for Calibre-Web to connect.

Create an application for Calibre-Web in authentik and follow the Forward auth documentation here https://goauthentik.io/docs/providers/proxy/forward_auth

## Calibre-Web

Login to Calibre-Web using an administrator account and go to Settings > Edit Basic Configuration. Under Feature Configuration, configure the following settings.

-   Tick Allow Reverse Proxy Authentication
-   Reverse Proxy Header Name: X-authentik-username
-   Login type: Use LDAP Authentication
-   LDAP Server Host Name or IP Address: Input the IP address or hostname of your authentik LDAP outpost
-   LDAP Server Port: 3389 (This may change depending on your configuration, most likely to 389)
-   LDAP Encryption: None
-   LDAP Authentication: Simple
-   LDAP Administrator Username: cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io
-   LDAP Administrator Password: Password for ldapservice account in authentik
-   LDAP User Object Filter: (&(cn=%s))
-   Tick LDAP Server is OpenLDAP?

Following Settings are Needed For User Import

-   LDAP Group Object Filter: (&(objectclass=group)(cn=%s))
-   LDAP Group Name: User group in authentik you'd like to import.
-   LDAP Group Name: member
-   LDAP Member User Filter Detection: Custom Filter
-   LDAP Member User Filter: (cn=%s)

Click Save

You must then go back to the main settings page and click Import LDAP Users
