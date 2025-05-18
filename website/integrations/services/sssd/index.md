---
title: Integrate with sssd
sidebar_label: sssd
support_level: community
---

## What is sssd

> **SSSD** is an acronym for System Security Services Daemon. It is the client component of centralized identity management solutions such as FreeIPA, 389 Directory Server, Microsoft Active Directory, OpenLDAP and other directory servers. The client serves and caches the information stored in the remote directory server and provides identity, authentication and authorization services to the host machine.
>
> -- https://sssd.io/

Note that authentik supports _only_ user and group objects. As
a consequence, it cannot be used to provide automount or sudo
configuration nor can it provide netgroups or services to `nss`.
Kerberos is also not supported.

## Preparation

The following placeholders are used in this guide:

- `authentik.company` is the FQDN of the authentik LDAP outpost installation.
- `ldap.baseDN` is the Base DN you configure in the LDAP provider.
- `ldap.domain` is (typically) an FQDN for your domain. Usually
  it is just the components of your base DN. For example, if
  `ldap.baseDN` is `dc=ldap,dc=goauthentik,dc=io` then the domain
  might be `ldap.goauthentik.io`.
- `ldap.searchGroup` is the "Search Group" that can can see all
  users and groups in authentik.
- `sssd.serviceAccount` is a service account created in authentik
- `sssd.serviceAccountToken` is the service account token generated
  by authentik.

:::note
This documentation lists only the settings that you need to change from their default values. Be aware that any changes other than those explicitly mentioned in this guide could cause issues accessing your application.
:::

:::warning
The provider configuration assumes that connections to the outpost use LDAPS, with properly configured certificates on both authentik and the host running sssd. LDAPS is the recommended protocol for secure communication. For details on setting up SSL and StartTLS on the outpost, refer to [authentik’s LDAP provider documentation](../../../docs/add-secure-apps/providers/ldap#ssl--starttls).
:::

## authentik configuration

Follow [official documentation](../../../docs/add-secure-apps/outposts/#create-and-configure-an-outpost) to create an **LDAP outpost**. If you already have an LDAP outpost configured, you can use it without additional setup. No further configuration in authentik is needed.

## sssd configuration

First, install the necessary sssd packages on your host. Very likely
the package is just `sssd`.

:::note
This guide well help you configure the `sssd.conf` for LDAP only. You
will likely need to perform other tasks for a usable setup
like setting up automounted or autocreated home directories that
are beyond the scope of this guide. See the "additional resources"
section for some help.
:::

Create a file at `/etc/sssd/sssd.conf` with contents similar to
the following:

```ini
[nss]
filter_groups = root
filter_users = root
reconnection_retries = 3

[sssd]
config_file_version = 2
reconnection_retries = 3
domains = ${ldap.domain}
services = nss, pam, ssh

[pam]
reconnection_retries = 3

[domain/${ldap.domain}]
cache_credentials = True
id_provider = ldap
chpass_provider = ldap
auth_provider = ldap
access_provider = ldap
ldap_uri = ldaps://${authentik.company}:636

ldap_schema = rfc2307bis
ldap_search_base = ${ldap.baseDN}
ldap_user_search_base = ou=users,${ldap.baseDN}
ldap_group_search_base = ${ldap.baseDN}

ldap_user_object_class = user
ldap_user_name = cn
ldap_group_object_class = group
ldap_group_name = cn

# Optionally, filter logins to only a specific group
#ldap_access_order = filter
#ldap_access_filter = memberOf=cn=authentik Admins,ou=groups,${ldap.baseDN}

ldap_default_bind_dn = cn=${sssd.serviceAccount},ou=users,${ldap.baseDN}
ldap_default_authtok = ${sssd.serviceAccountToken}
```

You should now be able to start sssd; however, the system may not
yet be setup to use it. Depending on your platform, you may need to
use `authconfig` or `pam-auth-update` to configure your system. See
the additional resources section for details.

:::note
You can store SSH authorized keys in LDAP by adding the
`sshPublicKey` attribute to any user with their public key as
the value.
:::

## Additional Resources

The setup of sssd may vary based on Linux distribution and version,
here are some resources that can help you get this setup:

:::note
authentik is providing a simple LDAP server, not an Active Directory
domain. Be sure you're looking at the correct sections in these guides.
:::

- https://sssd.io/docs/quick-start.html#quick-start-ldap
- https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/system-level_authentication_guide/configuring_services
- https://ubuntu.com/server/docs/service-sssd
- https://manpages.debian.org/unstable/sssd-ldap/sssd-ldap.5.en.html
- https://wiki.archlinux.org/title/LDAP_authentication
