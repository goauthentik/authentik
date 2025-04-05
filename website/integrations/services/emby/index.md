---
title: Integrate with Emby
sidebar_label: Emby
support_level: community
---

## What is Emby

> Emby is a free and media management and streaming platform for movies, TV shows, and music.
>
> -- https://emby.media/

:::note
[Emby Premiere](https://emby.media/premiere.html) is needed for LDAP authentication to work via the official Plugin.
:::

:::caution
An LDAP outpost must be deployed to use the Emby LDAP plugin
:::

## Preparation

The following placeholders are used in this guide:

- `emby.company` is the FQDN of the Emby installation.
- `authentik.company` is the FQDN of the authentik installation.
- `ldap.company` the FQDN of the LDAP outpost.
- `dc=company,dc=com` the Base DN of the LDAP provider.
- `ldap_bind_user` the username of the desired LDAP Bind User
- `emby_users` is the group which should have access to Emby.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

No additional authentik configuration needs to be configured. Follow the LDAP outpost instructions to create an LDAP outpost and configure access via the outpost.

1. If you don't have one already, create an LDAP bind user
2. Allow search access for the LDAP bind user on the application
    - Edit the provider
    - Select the tab **Permissions**
    - Select User **Object Permissions**
    - Select **Assign new user** and select you LDAP bind user with "Search full LDAP directory" and "Can view LDAP Provider" enabled
3. Add the LDAP bind user to the Application Bindings

## Emby configuration

1. Navigate to your Emby installation and log in with the admin account or currently configured local admin
2. Open the **Administrator dashboard** and go to the **Plugins** section
3. Click **Catalog** at the top of the page, and locate the "LDAP" plugin _(Needs Emby Premiere)_
4. Install the plugin. You may need to restart Emby to finish installation
5. Once finished, navigate back to the plugins section of the admin dashboard and click on the "LDAP" plugin icon to open the settings
6. Configure the LDAP Settings as follows:
    - `LDAP server address`: `ldap.company`
    - `LDAP server Port number`: `636`
    - `Enable SSL`: **Checked**
    - `SSL certificate thumbprint (SHA1):`:
        - Paste the SHA1 Fingerprint of your LDAP outpost Certificate here. It can be found on you Authentik Instance via **System** -> **Certificates**
    - `Bind DN`: `cn=ldap_bind_user,ou=users,dc=company,dc=com` _(Change to the LDAP bind user)_
    - `Bind credentials`: The Password of the user. If using a Service account, this is the token
    - `User search base`: The base DN for LDAP queries. To query all users, set this to `dc=company,dc=com`
        - You can specify an OU if you divide your users up into different OUs and only want to query a specific OU
    - `User search filter`: This is used to a user filter on what users are allowed to login. **This must be set**
        - To allow all users: `(&(objectClass=user)(cn={0})`
        - To only allow users in a specific group: `(&(objectClass=user)(memberOf=cn=emby_users,ou=groups,dc=company,dc=com)(cn={0}))` _(Change to the LDAP bind user)_
        - Good Docs on LDAP Filters: [atlassian.com](https://confluence.atlassian.com/kb/how-to-write-ldap-search-filters-792496933.html)

7. Click "Save"

## Configuration verification

Logout, and login with a LDAP user. Username **must** be used, logging in with email will not work

If there are issues with the login, you can try to debug your search filter. Good docs can be found here: [docs.goauthentik.io](https://docs.goauthentik.io/docs/add-secure-apps/providers/ldap/generic_setup#ldapsearch-test)
