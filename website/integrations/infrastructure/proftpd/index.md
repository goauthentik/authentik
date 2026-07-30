---
title: Integrate with ProFTPD
sidebar_label: ProFTPD
support_level: community
---

## What is ProFTPD

> ProFTPD is a high-performance, extremely configurable, and secure FTP server, featuring Apache-like configuration and blazing performance.
>
<<<<<<< HEAD
> -- From http://www.proftpd.org

This integration leverages authentik's LDAP for the identity provider to achieve an SSO experience. See [ldap provider generic setup](https://docs.goauthentik.io/docs/add-secure-apps/providers/ldap/generic_setup) for setting up the LDAP provider.
=======
> -- http://www.proftpd.org/
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik LDAP outpost.

This guide uses authentik's LDAP provider to authenticate ProFTPD users. ProFTPD must be able to reach the authentik LDAP outpost on the LDAP or LDAPS port that you expose.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik Configuration

To support the integration of ProFTPD with authentik, you need to create an LDAP search group, a service account, an LDAP provider, an application, and an LDAP outpost.

<<<<<<< HEAD
Create a new user account _(or reuse an existing one)_ for ProFTPD to use for LDAP bind under _Directory_ -> _Users_ -> _Create_ and give the account a name, such as `ldapservice`.

:::note
On default provider settings, the DN of this user will be `cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io`
=======
### Create an LDAP search group

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Directory** > **Groups** and click **Create**.
3. Enter `LDAP search` as the name and click **Create**.

### Create a service account

1. Navigate to **Directory** > **Users** and click **Create a service account**.
2. Enter `ldapservice` as the username and click **Create**.
3. Copy the generated token. If you need to create another token later, navigate to **Directory** > **Tokens and App passwords** and click **Create**.
4. Navigate to **Directory** > **Groups**, click **LDAP search**, and open the **Users** tab.
5. Click **Add existing user**, select **ldapservice**, and click **Add**.

:::info LDAP bind accounts
A bind account authenticates the LDAP client to the LDAP server so the client can search for users and groups.
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))
:::

### Create an LDAP provider

<<<<<<< HEAD
:::note
_If you are unfamiliar with LDAP_: A bind account is used for authentication against the LDAP server itself - similar to an API key in modern applications.
:::
=======
1. Navigate to **Applications** > **Providers** and click **Create**.
2. Select **LDAP Provider** as the provider type.
3. Configure the following values:
    - **Name**: enter a descriptive name.
    - **Base DN**: enter the LDAP base DN for your environment and note it for the ProFTPD configuration.
    - **Search group**: select **LDAP search**.
    - **Certificate**: select the certificate that your LDAP clients should trust for LDAPS.
4. Click **Finish**.
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

### Create an application

1. Navigate to **Applications** > **Applications** and click **Create**.
2. Configure the following values:
    - **Name**: enter a descriptive name.
    - **Provider**: select the LDAP provider that you created.
3. Click **Create**.
4. Open the application, click the **Users** tab, and click **Add existing user**.
5. Select **ldapservice** and click **Add**.

### Create or update an LDAP outpost

1. Navigate to **Applications** > **Outposts**.
2. Create an LDAP outpost or edit an existing LDAP outpost.
3. Add the LDAP application that you created to the outpost.
4. Deploy the outpost where the ProFTPD host can reach it.

### Restrict FTP access _(optional)_

To restrict FTP access to specific users, create a group such as `ftpusers` and add only the allowed users to that group. The ProFTPD configuration below shows a group filter that uses this group.

## ProFTPD configuration

Install the ProFTPD LDAP plugin if it is packaged separately for your distribution. The package is commonly named `proftpd-ldap`.

Check that `LoadModule mod_ldap.c` is enabled in `/etc/proftpd/modules.conf`.

Edit the ProFTPD configuration file. Depending on your distribution, this file is usually `/etc/proftpd.conf` or `/etc/proftpd/proftpd.conf`.

```apacheconf title="/etc/proftpd/proftpd.conf"
DefaultRoot /your/ftp/storage/dir

<IfModule mod_ldap.c>
    LDAPAuthBinds on
    LDAPServer authentik.company:389
<<<<<<< HEAD
    # The LDAP Bind account must be specified here
    LDAPBindDN cn=ldapservice,ou=users,dc=ldap,dc=goauthentik,dc=io PASSWORDOFLDAPSERVICE
    # The second parameter is optional
    #  In this case I am restricting access to the group ftpusers
    #  Instead you could also create bind policies in your created authentik application
    LDAPUsers ou=users,dc=ldap,dc=goauthentik,dc=io (&(objectClass=user)(cn=%u)(memberOf=cn=ftpusers,ou=groups,dc=ldap,dc=goauthentik,dc=io))
=======
    LDAPBindDN cn=ldapservice,ou=users,<base_dn> <service_account_token>
    LDAPUsers ou=users,<base_dn> (&(objectClass=user)(cn=%u)(memberOf=cn=ftpusers,ou=groups,<base_dn>))
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

    LDAPDefaultUID 1000
    LDAPDefaultGID 1000
    LDAPForceDefaultUID on
    LDAPForceDefaultGID on

    LDAPGenerateHomedir on
    LDAPGenerateHomedirPrefix /your/ftp/storage/dir
    LDAPGenerateHomedirPrefixNoUsername on

    LDAPLog /var/log/mod_ldap.log

    RequireValidShell off

    LDAPAttr uid cn

    LDAPSearchScope subtree
</IfModule>
```

The example maps every FTP login to the local Linux user and group ID `1000` and uses a shared home directory. Ensure that the local user and group exist and can access `/your/ftp/storage/dir`.

If you want each user to have a separate home directory, remove `LDAPGenerateHomedirPrefixNoUsername on` and configure the home directory behavior for your environment.

<<<<<<< HEAD
If you do not set `LDAPForceDefaultUID`/`LDAPForceDefaultGID`, Authentik's `uidNumber` field will be used. If you do not set `LDAPGenerateHomedir`, Authentik's `homeDirectory` field will be used (`/home/$username`). For more information about default attributes provided by Authentik, refer to the [LDAP Provider documentation](https://docs.goauthentik.io/docs/add-secure-apps/providers/ldap).
=======
If you do not configure `LDAPForceDefaultUID` and `LDAPForceDefaultGID`, ProFTPD uses the `uidNumber` and `gidNumber` values returned by authentik. If you do not configure `LDAPGenerateHomedir`, ProFTPD uses each user's `homeDirectory` value.
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))

Restart ProFTPD for the changes to take effect.

## Configuration verification

<<<<<<< HEAD
:::note
If login fails, make sure to check the logs of the LDAP plugin: `tail -f /var/log/mod_ldap.log`.
:::
=======
To confirm that authentik is properly configured with ProFTPD, connect to the FTP server with an authentik user that is allowed by the LDAP filter.

If login fails, check the LDAP plugin log:

```bash
tail -f /var/log/mod_ldap.log
```

## Resources

- [ProFTPD project website](http://www.proftpd.org/)
- [ProFTPD mod_ldap documentation](http://www.proftpd.org/docs/contrib/mod_ldap.html)
>>>>>>> a690485a1 (website/docs: release 2026.8: fix missing headers (#24522))
