---
title: LDAP Outpost
---

:::info
This feature is still in technical preview, so please report any Bugs you run into on [GitHub](https://github.com/goauthentik/authentik/issues)
:::

You can configure an LDAP Provider for applications that don't support any newer protocols or require LDAP.

All users and groups in authentik's database are searchable. Currently, there is a limited support for filters (you can only search for objectClass), but this will be expanded in further releases.

Binding against the LDAP Server uses a flow in the background. This allows you to use the same policies and flows as you do for web-based logins. The only limitation is that currently only identification and password stages are supported, due to how LDAP works.

You can configure under which base DN the information should be available. For this documentation we'll use the default of `DC=ldap,DC=goauthentik,DC=io`.

Users are available under `ou=users,<base DN>` and groups under `ou=groups,<base DN>`.

You can bind using the DN `cn=<username>,ou=users,<base DN>`, or using the following ldapsearch command for example:

```
ldapsearch \
  -x \ # Only simple binds are currently supported
  -h *ip* \
  -p 3389 \
  -D 'cn=*user*,ou=users,DC=ldap,DC=goauthentik,DC=io' \ # Bind user and password
  -w '*password*' \
  -b 'ou=users,DC=ldap,DC=goauthentik,DC=io' \ # The search base
  '(objectClass=user)'
```

The following fields are currently sent for users:

- `cn`: User's username
- `uid`: Unique user identifier
- `name`: User's name
- `displayName`: User's name
- `mail`: User's email address
- `objectClass`: A list of these strings:
  - "user"
  - "organizationalPerson"
  - "goauthentik.io/ldap/user"
- `accountStatus`: "active" if the account is active, otherwise "inactive"
- `superuser`: "active" if the account is part of a group with superuser permissions, otherwise "inactive"
- `memberOf`: A list of all DNs that the user is a member of

The following fields are current set for groups:

- `cn`: The group's name
- `uid`: Unique group identifier
- `objectClass`: A list of these strings:
  - "group"
  - "goauthentik.io/ldap/group"

**Additionally**, for both users and groups, any attributes you set are also present as LDAP Attributes.
