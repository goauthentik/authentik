---
title: Jellyfin
---

<span class="badge badge--secondary">Support level: Community</span>

## What is Jellyfin

> Jellyfin is a free and open source media management and streaming platform for movies, TV shows, and music.
>
> -- https://jellyfin.org

:::note
Jellyfin does not have any native external authentication support as of the writing of this page.
:::

:::note
Currently there are two plugins for Jelyfin that provide external authenticaion, an OIDC plugin and an LDAP plugin. This guide focuses on the use of the LDAP plugin.
:::

:::caution
An LDAP outpost must be deployed to use the Jellyfin LDAP plugin
:::

## Preparation

The following placeholders will be used:

-   `jellyfin.company.com` is the FQDN of the Jellyfin install.
-   `authentik.company.com` is the FQDN of the authentik install.
-   `ldap.company.com` the FQDN of the LDAP outpost.
-   `dc=company,dc=com` the Base DN of the LDAP outpost.
-   `ldap_bind_user` the username of the desired LDAP Bind User

## Service Configuration

1. If you don't have one already create an LDAP bind user before starting these steps.
    - Ideally, this user doesn't have any permissions other than the ability to view other users. However, some functions do require an account with permissions.
    - This user must be part of the group that is specified in the "Search group" in the LDAP outpost.
2. Navigate to your Jellyfin installation and log in with the admin account or currently configured local admin.
3. Open the administrator dashboard and go to the "Plugins" section.
4. Click "Catalog" at the top of the page, and locate the "LDAP Authentication Plugin"
5. Install the plugin. You may need to restart Jellyfin to finish installation.
6. Once finished navigate back to the plugins section of the admin dashboard, click the 3 dots on the "LDAP-Auth Plugin" card, and click settings.
7. Configure the LDAP Settings as follows:
    - `LDAP Server`: `ldap.company.com`
    - `LDAP Port`: 636
    - `Secure LDAP`: **Checked**
    - `StartTLS`: Unchecked
    - `Skip SSL/TLS Verification`:
        - If using a certificate issued by a certificate authority Jellyfin trusts, leave this unchecked.
        - If you're using a self signed certificate, check this box.
    - `Allow password change`: Unchecked
        - Since authentik already has a frontend for password resets, its not necessary to include this in Jellyfin, especially since it requires bind user to have privileges.
    - `Password Reset URL`: Empty
    - `LDAP Bind User`: Set this to a the user you want to bind to in authentik. By default the path will be `ou=users,dc=company,dc=com` so the LDAP Bind user will be `cn=ldap_bind_user,ou=users,dc=company,dc=com`.
    - `LDAP Bind User Password`: The Password of the user. If using a Service account, this is the token.
    - `LDAP Base DN for Searches`: the base DN for LDAP queries. To query all users set this to `dc=company,dc=com`.
        - You can specify an OU if you divide your users up into different OUs and only want to query a specific OU.

At this point click `Save and Test LDAP Server Settings`. If the settings are correct you will see:
`Connect(Success); Bind(Success); Base Search (Found XY Entities)`

-   `LDAP User Filter`: This is used to a user filter on what users are allowed to login. **This must be set**
    -   To allow all users: `(objectClass=user)`
    -   To only allow users in a specific group: `(memberOf=cn=jellyfin_users,ou=groups,dc=company,dc=com)`
    -   Good Docs on LDAP Filters: [atlassian.com](https://confluence.atlassian.com/kb/how-to-write-ldap-search-filters-792496933.html)
-   `LDAP Admin Base DN`: All of the users in this DN are automatically set as admins.
    -   This can be left blank. Admins can be set manually outside of this filter
-   `LDAP Admin Filter`: Similar to the user filter, but every matched user is set as admin.
    -   This can be left blank. Admins can be set manually outside of this filter

At this point click `Save and Test LDAP Filter Settings`. If the settings are correct you will see:
`Found X user(s), Y admin(s)`

-   `LDAP Attributes`: `uid, cn, mail, displayName`
-   `Enable case Insensitive Username`: **Checked**

At this point, enter in a username and click "Save Search Attribute Settings and Query User". If the settings are correct you will see:
`Found User: cn=test,ou=users,dc=company,dc=com`

-   `Enabled User Creation`: **Checked**
-   `LDAP Name Attribute`: `cn`
-   `LDAP Password Attribute`: `userPassword`
-   `Library Access`: Set this according to desired library access

1. Click "Save"
2. Logout, and login with a LDAP user. Username **must** be used, logging in with email will not work.

## authentik Configuration

No additional authentik configuration needs to be configured. Follow the LDAP outpost instructions to create an LDAP outpost and configure access via the outpost
