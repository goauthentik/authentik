---
title: Calibre-WEB
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Calibre Web

From https://github.com/janeczku/calibre-web

:::note
Web app for browsing, reading and downloading eBooks stored in a Calibre database.
:::

:::warning
An LDAP outpost must be deployed to use the Calibre LDAP connection
:::

## Preparation

The following placeholders will be used:

-   `ldap.company.com` the FQDN of the LDAP outpost.
-   `dc=company,dc=com` the Base DN of the LDAP outpost.
-   `ldap_bind_user` the username of the desired LDAP Bind User

## Service Configuration

1. If you don't have one already create an LDAP bind user before starting these steps.
    - Ideally, this user doesn't have any permissions other than the ability to view other users. However, some functions do require an account with permissions.
    - This user must be part of the group that is specified in the "Search group" in the LDAP outpost.
2. Navigate to your Calibre Web installation and log in with the admin account or currently configured local admin.
3. Open the admin panel and press `Edit Basic Configuration`
4. Scroll to `Feature Configuration`
5. Configure it as follows:
    - `Login Type`: Use LDAP Authentication
    - `LDAP Server Host Name or IP Address`: `ldap.company.com`
    - `LDAP Port`: 3389
    - `LDAP Encryption`: None
    - `LDAP Authentication`: Simple
    - `LDAP Administrator Username`: Set this to a the user you want to bind to in authentik. By default the path will be `ou=users,dc=company,dc=com` so the LDAP Bind user will be `cn=ldap_bind_user,ou=users,dc=company,dc=com`.
    - `LDAP Administrator Password`: The Password of the user. If using a Service account, this is the token.
    - `LDAP Distinguished Name (DN)`: `dc=company,dc=com`
    - `LDAP User Object Filter`: `cn=%s`
    - `LDAP Server is OpenLDAP?`: Ticked, otherwise login fails
    - `LDAP Group Object Filter`: `(&(objectclass=group)(cn=%s))`
    - `LDAP Group Name`: Set this to the name of the group you want to import users from
    - `LDAP Group Members Field`: `member`
    - `LDAP Member User Filter Detection`: Autodetect
6. Click `Save`
7. Go back to the admin panel and press `Import LDAP users`. You should see users from LDAP group appearing in your calibre web server.
8. Logout and login with your LDAP user credentials. It should authenticate successfully.

## authentik Configuration

No additional authentik configuration needs to be configured. Follow the LDAP outpost instructions to create an LDAP outpost and configure access via the outpost
