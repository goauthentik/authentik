---
title: LDAP Provider
---

:::info
This feature is still in technical preview, so please report any Bugs you run into on [GitHub](https://github.com/goauthentik/authentik/issues)
:::

You can configure an LDAP Provider for applications that don't support any newer protocols or require LDAP.

:::info
Note: This provider requires the deployment of the [LDAP Outpost](../outposts/outposts.md)
:::

All users and groups in authentik's database are searchable. Currently, there is limited support for filters (you can only search for objectClass), but this will be expanded in further releases.

Binding against the LDAP Server uses a flow in the background. This allows you to use the same policies and flows as you do for web-based logins. The only limitation is that currently only identification and password stages are supported, due to how LDAP works.

You can configure under which base DN the information should be available. For this documentation we'll use the default of `DC=ldap,DC=goauthentik,DC=io`.

Users are available under `ou=users,<base DN>` and groups under `ou=groups,<base DN>`. To aid compatibility, each user belongs to its own "virtual" group, as is standard on most Unix-like systems. This group does not exist in the authentik database, and is generated on the fly. These virtual groups are under the `ou=virtual-groups,<base DN>` DN.

You can bind using the DN `cn=<username>,ou=users,<base DN>`, or using the following ldapsearch command for example:

```
ldapsearch \
  -x \ # Only simple binds are currently supported
  -h *ip* \
  -p 389 \
  -D 'cn=*user*,ou=users,DC=ldap,DC=goauthentik,DC=io' \ # Bind user and password
  -w '*password*' \
  -b 'ou=users,DC=ldap,DC=goauthentik,DC=io' \ # The search base
  '(objectClass=user)'
```

The following fields are currently sent for users:

- `cn`: User's username
- `uid`: Unique user identifier
- `uidNumber`: A unique numeric identifier for the user
- `name`: User's name
- `displayName`: User's name
- `mail`: User's email address
- `objectClass`: A list of these strings:
  - "user"
  - "organizationalPerson"
  - "goauthentik.io/ldap/user"
- `memberOf`: A list of all DNs that the user is a member of
- `goauthentik.io/ldap/active`: "true" if the account is active, otherwise "false"
- `goauthentik.io/ldap/superuser`: "true" if the account is part of a group with superuser permissions, otherwise "false"

The following fields are current set for groups:

- `cn`: The group's name
- `uid`: Unique group identifier
- `gidNumber`: A unique numeric identifier for the group
- `member`: A list of all DNs of the groups members
- `objectClass`: A list of these strings:
  - "group"
  - "goauthentik.io/ldap/group"

A virtual group is also created for each user, they have the same fields as groups but have an additional objectClass: `goauthentik.io/ldap/virtual-group`.
The virtual groups gidNumber is equal to the uidNumber of the user.

**Additionally**, for both users and (non-virtual) groups, any attributes you set are also present as LDAP Attributes.

:::info
Starting with 2021.9.1, custom attributes will override the inbuilt attributes.
:::

## SSL

You can also configure SSL for your LDAP Providers by selecting a certificate and a server name in the provider settings.

This enables you to bind on port 636 using LDAPS, StartTLS is not supported.

## Example: sssd

[sssd](https://sssd.io/) is a common method of retrieving users and groups on a Linux host from an LDAP server. The below
`sssd.conf` can be used to do so against an Authentik LDAP provider:

```ini
[nss]
filter_groups = root
filter_users = root
reconnection_retries = 3

[sssd]
config_file_version = 2
reconnection_retries = 3
sbus_timeout = 30
domains = ldap.goauthentik.io
services = nss, pam, ssh

[pam]
reconnection_retries = 3

[domain/ldap.goauthentik.io]
cache_credentials = True
id_provider = ldap
chpass_provider = ldap
auth_provider = ldap
access_provider = ldap
ldap_uri = ldaps://*ip*:636

ldap_schema = rfc2307bis
ldap_search_base = dc=ldap,dc=goauthentik,dc=io
ldap_user_search_base = ou=users,dc=ldap,dc=goauthentik,dc=io
ldap_group_search_base = dc=ldap,dc=goauthentik,dc=io

ldap_user_object_class = user
ldap_user_name = cn
ldap_group_object_class = group
ldap_group_name = cn

# Optionally, filter logins to only a specific group
#ldap_access_order = filter
#ldap_access_filter = memberOf=cn=authentik Admins,ou=groups,dc=ldap,dc=goauthentik,dc=io

ldap_default_bind_dn = cn=service-sssd,ou=users,dc=ldap,dc=goauthentik,dc=io
ldap_default_authtok = *token-from-authentik*
```

You'll first need to create a service account like the above. Setting up sssd on a given
distribution varies, please consult the documentation for that specific distribution.

You can store SSH authorized keys in LDAP by adding the `sshPublicKey` attribute to any
user with their public key as the value.
