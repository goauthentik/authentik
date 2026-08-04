---
title: Integrate with ProFTPD
sidebar_label: ProFTPD
support_level: community
---

## What is ProFTPD?

> ProFTPD is a high-performance, extremely configurable, and secure FTP server, featuring Apache-like configuration and blazing performance.
>
> -- http://www.proftpd.org/

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik LDAP outpost.

This guide uses authentik's LDAP provider to authenticate ProFTPD users. ProFTPD must be able to reach the authentik LDAP outpost on the LDAP or LDAPS port that you expose.

:::info
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

## authentik configuration

To support the integration of ProFTPD with authentik, you need to create an LDAP search group, a service account, an LDAP provider, an application, and an LDAP outpost.

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
:::

### Create an LDAP provider

1. Navigate to **Applications** > **Providers** and click **Create**.
2. Select **LDAP Provider** as the provider type.
3. Configure the following values:
    - **Name**: enter a descriptive name.
    - **Base DN**: enter the LDAP base DN for your environment and note it for the ProFTPD configuration.
    - **Search group**: select **LDAP search**.
    - **Certificate**: select the certificate that your LDAP clients should trust for LDAPS.
4. Click **Finish**.

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
    LDAPBindDN cn=ldapservice,ou=users,<base_dn> <service_account_token>
    LDAPUsers ou=users,<base_dn> (&(objectClass=user)(cn=%u)(memberOf=cn=ftpusers,ou=groups,<base_dn>))

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

If you do not configure `LDAPForceDefaultUID` and `LDAPForceDefaultGID`, ProFTPD uses the `uidNumber` and `gidNumber` values returned by authentik. If you do not configure `LDAPGenerateHomedir`, ProFTPD uses each user's `homeDirectory` value.

Restart ProFTPD for the changes to take effect.

## Configuration verification

To confirm that authentik is properly configured with ProFTPD, connect to the FTP server with an authentik user that is allowed by the LDAP filter.

If login fails, check the LDAP plugin log:

```bash
tail -f /var/log/mod_ldap.log
```

## Resources

- [ProFTPD project website](http://www.proftpd.org/)
- [ProFTPD mod_ldap documentation](http://www.proftpd.org/docs/contrib/mod_ldap.html)
