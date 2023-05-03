---
title: ProFTPD
---

<span class="badge badge--secondary">Support level: Community</span>

## What is ProFTPD

:::note
ProFTPD is a high-performance, open-source FTP server software designed for Unix and Linux systems. It supports various features, including IPv6, SSL/TLS encryption, virtual hosting, advanced logging, and supports various authentication methods, including LDAP and MySQL.
:::

This integration leverages authentik's LDAP for the identity provider to achieve an SSO experience. See [ldap provider generic setup](../../../docs/providers/ldap/generic_setup) for setting up the LDAP provider.

## Preparation

The following placeholders will be used:

-   `authentik.company` is the FQDN of the authentik install.

## authentik Configuration

### Step 1 - Service account

Create a new user account _(or re-use an existing one)_ for ProFTPD to use for LDAP bind under _Directory_ -> _Users_ -> _Create_ and give the account a name, such as `ldapservice`.

:::note
On default provider settings, the DN of this user will be `cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io`
:::

This user must be part of a group which allows LDAP search queries. If you don't have a group for that yet, create one (e.g. `LDAPServiceUsers`) and add the user `ldapservice` to that group. You can specify that group during the provider creation below.

:::note
_If you are unfamiliar with LDAP_: A bind account is used for authentication against the LDAP server itself - similar to an API key in modern applications.
:::

### Step 2 - LDAP Provider

In authentik, create a LDAP provider (under _Applications/Providers_). This is an example for the settings:

-   Name : `provider-ldap` - or choose any
-   Bind DN : `DC=ldap,DC=goauthentik,DC=io`
-   Search group : `LDAPServiceUsers`
-   Certificate : `authentik Self-signed Certificate`

### Step 3 - Application

In authentik, create an application (under _Resources/Applications_) with these settings :

-   Name: `FTP` - or choose any
-   Provider: Choose the provider you created in _Step 2_

### Step 4 - Outpost

If not done yet, create an outpost (under _Applications/Outposts_) of type `LDAP` that includes the LDAP Application you created in _Step 3_. You can also use an existing outpost, just make sure to edit it and to also include the just created application in the respective field.

### Step 5 - Create a group for restricting access

_Optionally_, create a new group like `ftpusers` to scope access to the ftp server.

## ProFTPD configuration

Ensure that the ProFTPD LDAP plugin is installed, which may be included in the distribution package `proftpd-ldap`.

Check that `LoadModule mod_ldap.c` is not commented out in `/etc/proftpd/modules.conf`.

Edit your ProFTPD configuration, usually located under `/etc/proftpd.conf`. You can use the following LDAP configuration as a starting point.

```bash
DefaultRoot /your/ftp/storage/dir

<IfModule mod_ldap.c>
    LDAPAuthBinds on
    # Replace this with the server-url:port of your LDAP outpost
    LDAPServer authentik.company:389
    # The LDAP Bind account must be specified here
    LDAPBindDN cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io PASSWORDOFLDAPSERVICE
    # The second parameter is optional
    #  In this case I am restricting access to the group ftpusers
    #  Instead you could also create bind policies in your created authentik application
    LDAPUsers ou=users,dc=ldap,dc=goauthentik,dc=io (&(objectClass=user)(cn=%u)(memberOf=cn=ftpusers,ou=groups,dc=ldap,dc=goauthentik,dc=io))

    # In this example, I am forcing the permission of all files to the system user/group 1000
    LDAPDefaultUID 1000
    LDAPDefaultGID 1000
    LDAPForceDefaultUID on
    LDAPForceDefaultGID on

    # This way I am making a shared folder, which all ftp users share
    LDAPGenerateHomedir on
    LDAPGenerateHomedirPrefix /your/ftp/storage/dir
    LDAPGenerateHomedirPrefixNoUsername on

    LDAPLog /var/log/mod_ldap.log

    RequireValidShell off

    LDAPAttr uid cn

    LDAPSearchScope subtree
</IfModule>
```

In this example, every user shares a single folder. If you want to have separate folders for each user, you can adapt the `LDAPGenerateHomedirPrefixNoUsername` setting.

Additionally, note that each file will have Linux user and group ID `1000`. Beforehand, make sure that the respective Linux user exists (usually the first Linux user created receives ID `1000`). Check `/etc/passwd` and create a user if necessary.

If you do not set `LDAPForceDefaultUID`/`LDAPForceDefaultGID`, Authentik's `uidNumber` field will be used. If you do not set `LDAPGenerateHomedir`, Authentik's `homeDirectory` field will be used (`/home/$username`). For more information about default attributes provided by Authentik, refer to the [LDAP Provider documentation](../../../docs/providers/ldap).

Make sure to read ProFTPD's [available LDAP options](http://www.proftpd.org/docs/contrib/mod_ldap.html).

Finally, after adding the configuration, restart ProFTPD.

:::note
If login fails, make sure to check the logs of the LDAP plugin: `tail -f /var/log/mod_ldap.log`.
:::
