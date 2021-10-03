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
