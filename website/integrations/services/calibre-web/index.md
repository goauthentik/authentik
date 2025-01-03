---
title: Integrate with Calibre-Web
sidebar_label: Calibre-Web
---

# Calibre-Web

<span class="badge badge--secondary">Support level: Community</span>

## What is Calibre-Web

> Calibre-Web is a web app that offers a clean and intuitive interface for browsing, reading, and downloading eBooks using a valid Calibre database.
>
> -- https://github.com/janeczku/calibre-web

## Preparation

The following placeholders will be used:

- `ldapservice` is the username of the authentik administrator user you'd like to use for Calibre-Web connection.
- `authentik.company` is the FQDN of the authentik install.

## authentik configuration

Insert authentik configuration

1. Write first step here...

2. Continue with steps....

## Calibre-Web configuration

Login into your Calibre-Web instance using an administrator account and go to **Settings** -> **Edit Basic Configuration**. Under **Feature Configuration**, configure the following settings:

- Allow Reverse Proxy Authentication: Ticked
- Reverse Proxy Header Name: `X-authentik-username`
- Login type: `Use LDAP Authentication`
- LDAP Server Host Name or IP Address: Set this to the IP address or hostname of your authentik LDAP outpost
- LDAP Server Port: Set this to the LDAP port you configured for your outpost
- LDAP Encryption: `None`
- LDAP Authentication: `Simple`
- LDAP Administrator Username: `cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io`
- LDAP Administrator Password: Set this to the password of your `ldapservice` account
- LDAP User Object Filter: `(&(cn=%s))`
- LDAP Group Object Filter: `(&(objectclass=group)(cn=%s))`
- LDAP Group Name: User group in authentik you'd like to import. Most likely to be `users`
- LDAP Member User Filter Detection: `Custom Filter`
- LDAP Member User Filter: `(cn=%s)`

You must then go back to the main settings page and click **Import LDAP Users**.

