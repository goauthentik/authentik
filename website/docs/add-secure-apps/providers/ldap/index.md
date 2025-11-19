---
title: LDAP Provider
toc_max_heading_level: 5
---

The LDAP provider allows you to integrate with Service Providers using LDAP. It supports secure connections via LDAPS, code-based MFA authentication, basic LDAP schema compatibility, and can also be integrated with [SSSD](/integrations/services/sssd/) for authentication on Linux-based systems.

Refer to our documentation to learn how to [create a LDAP provider](./generic_setup.md).

## LDAP directory

All users and groups in authentik's database are searchable via the LDAP directory served by the LDAP provider.

### Base DN

You can configure under which **Base DN** the LDAP directory should be available. The default is: `DC=ldap,DC=goauthentik,DC=io`

The setting is available under **Protocol settings** on the LDAP provider.

:::info Base DN when using multiple LDAP providers
When using multiple LDAP providers, each LDAP provider must have a unique Base DN. You can achieve this by prepending an application-specific OU or DC. e.g. `OU=appname,DC=ldap,DC=goauthentik,DC=io`
:::

### Users

Users are located under: `ou=users,<base DN>`

To aid compatibility, each user belongs to its own "virtual" group, as is standard on most Unix-like systems. This group does not exist in the authentik database, and is generated on the fly. These virtual groups are located under the `ou=virtual-groups,<base DN>` DN. They have the same attributes as groups but have an additional `objectClass`: `goauthentik.io/ldap/virtual-group`. The `gidNumber` attribute of each virtual group is equal to the `uidNumber` of the user.

The following attributes are returned for users:

| Attribute       | Description                                                                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cn`            | User's username                                                                                                                                           |
| `uid`           | Unique user identifier                                                                                                                                    |
| `uidNumber`     | A unique numeric identifier for the user                                                                                                                  |
| `name`          | User's name                                                                                                                                               |
| `displayName`   | User's display name                                                                                                                                       |
| `mail`          | User's email address                                                                                                                                      |
| `objectClass`   | List of these strings: "user", "organizationalPerson", "goauthentik.io/ldap/user"                                                                         |
| `memberOf`      | List of all DNs that the user is a member of                                                                                                              |
| `homeDirectory` | Default home directory path for the user, by default `/home/$username`. Can be overwritten by setting `homeDirectory` as an attribute on users or groups. |
| `ak-active`     | `true` if the account is active, otherwise `false`                                                                                                        |
| `ak-superuser`  | `true` if the account is part of a group with superuser permissions, otherwise `false`                                                                    |

:::info Custom attributes
Any custom attributes you set are also returned as LDAP attributes. Built-in attributes will be overwritten by custom attributes with matching names. Periods and slashes in custom attributes are sanitized.
:::

### Groups

Groups are located under: `ou=groups,<base DN>`

The following attributes are returned for groups:

| Attribute     | Description                                                                                          |
| ------------- | ---------------------------------------------------------------------------------------------------- |
| `cn`          | The group's name                                                                                     |
| `uid`         | Unique group identifier                                                                              |
| `gidNumber`   | Unique numeric identifier for the group                                                              |
| `member`      | List of all DNs of the group's members, including groups which have this group as their parent group |
| `memberOf`    | The DN of the parent group if this group has a parent group                                          |
| `objectClass` | List of these strings: "group", "goauthentik.io/ldap/group"                                          |

:::info Custom attributes
Any custom attributes you set are also returned as LDAP attributes. Built-in attributes will be overwritten by custom attributes with matching names. Periods and slashes in custom attributes are sanitized.
:::

## LDAPS via SSL or StartTLS

The LDAP provider supports secure connections via LDAPS using SSL or StartTLS.

You can configure SSL or StartTLS by configuring the **Certificate** and **TLS Server Name** settings on the provider.

The provider will pick the correct certificate based on the configured **TLS Server name** setting. The certificate is not picked based on the **Bind DN**, because the StartTLS operation should occur before the bind request to ensure that bind credentials are transmitted over TLS.

Configuring SSL or StartTLS enables you to bind on port 636 using LDAPS.

## Binding

Binding against the LDAP provider uses a flow in the background. This allows you to use the same policies and flows as you do for web-based logins.

The **Bind flow** determines the flow used for binding/authenticating users, and the **Unbind flow** determines the flow used when unbinding/de-authenticating users. Each is set under **Flow Settings** on the LDAP provider.

The following flow stages are supported by the LDAP provider:

- [Identification stage](../../flows-stages/stages/identification/index.mdx)
- [Password stage](../../flows-stages/stages/password/index.md)
- [Authenticator validation stage](../../flows-stages/stages/authenticator_validate/index.mdx)
- [User Logout stage](../../flows-stages/stages/user_logout.md)
- [User Login stage](../../flows-stages/stages/user_login/index.md)
- [Deny stage](../../flows-stages/stages/deny.md)

### Bind modes

The LDAP provider supports two different bind modes:

#### Direct bind

In this mode, the outpost will always execute the configured flow when a new bind request is received.

#### Cached bind

This mode uses the same logic as direct bind, however the result is cached for the entered credentials, and saved in memory for the standard session duration. Sessions are saved independently, meaning that revoking sessions does _not_ remove them from the outpost, and neither will changing a users credentials.

## Searching

Any user that is authorized to access the LDAP provider's application can search the LDAP directory. Without explicit permissions to do broader searches, a user's search request will return information about themselves, including user info, group info, and group membership.

[Users](../../../users-sources/user/index.mdx) and [roles](../../../users-sources/roles/index.md) can be assigned the permission `Search full LDAP directory` to allow them to search the full LDAP directory and retrieve information about all users in the authentik instance.

:::info
Up to authentik version 2024.8 this was managed using the LDAP provider's **Search group** setting, where users could be added to a group to grant them this permission. With authentik 2024.8 this is automatically migrated to the `Search full LDAP directory` permission, which can be assigned more flexibly.
:::

### Search modes

The LDAP provider supports two different search modes:

#### Direct search

In this mode, every LDAP search request will trigger one or more requests to the authentik core API. This will always return the latest data, however this has a performance hit due to all the layers the backend requests have to go through.

#### Cached search

In this mode, the outpost will periodically fetch all users and groups from the backend, hold them in memory, and respond to search queries directly. This means greatly improved performance but potentially returning old/invalid data.

## Code-based MFA support

:::info Authenticator support
Authenticator validation currently only supports DUO, TOTP and static authenticators. SMS-based authenticators are not supported as they require a code to be sent from authentik, which is not possible during the bind.
:::

The LDAP provider supports code-based MFA.

Code-based authenticators are only supported when the **Code-based MFA Support** setting is enabled on the provider and the configured **Bind flow** includes a [Authenticator Validation stage](../../flows-stages/stages/authenticator_validate/index.mdx).

When enabled, all users that bind to the LDAP provider should have a supported authenticator configured, as otherwise a password might be incorrectly rejected if it contains a semicolon.

For code-based authenticators, the code must be given as part of the bind/authentication password, separated by a semicolon.

For example, for the password `example-password` and the MFA code `123456`, the input must be `example-password;123456`.
