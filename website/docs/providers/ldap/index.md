---
title: LDAP Provider
---

You can configure an LDAP Provider for applications that don't support any newer protocols or require LDAP.

:::info
Note: This provider requires the deployment of the [LDAP Outpost](../../outposts/)
:::

All users and groups in authentik's database are searchable. Currently, there is limited support for filters (you can only search for objectClass), but this will be expanded in further releases.

Binding against the LDAP Server uses a flow in the background. This allows you to use the same policies and flows as you do for web-based logins. For more info, see [Bind modes](#bind-modes).

You can configure under which base DN the information should be available. For this documentation we'll use the default of `DC=ldap,DC=goauthentik,DC=io`.

Users are available under `ou=users,<base DN>` and groups under `ou=groups,<base DN>`. To aid compatibility, each user belongs to its own "virtual" group, as is standard on most Unix-like systems. This group does not exist in the authentik database, and is generated on the fly. These virtual groups are under the `ou=virtual-groups,<base DN>` DN.

The following fields are currently sent for users:

-   `cn`: User's username
-   `uid`: Unique user identifier
-   `uidNumber`: A unique numeric identifier for the user
-   `name`: User's name
-   `displayName`: User's name
-   `mail`: User's email address
-   `objectClass`: A list of these strings:
    -   "user"
    -   "organizationalPerson"
    -   "goauthentik.io/ldap/user"
-   `memberOf`: A list of all DNs that the user is a member of
-   `homeDirectory`: A default home directory path for the user, by default `/home/$username`. Can be overwritten by setting `homeDirectory` as an attribute on users or groups.
-   `ak-active`: "true" if the account is active, otherwise "false"
-   `ak-superuser`: "true" if the account is part of a group with superuser permissions, otherwise "false"

The following fields are current set for groups:

-   `cn`: The group's name
-   `uid`: Unique group identifier
-   `gidNumber`: A unique numeric identifier for the group
-   `member`: A list of all DNs of the groups members
-   `objectClass`: A list of these strings:
    -   "group"
    -   "goauthentik.io/ldap/group"

A virtual group is also created for each user, they have the same fields as groups but have an additional objectClass: `goauthentik.io/ldap/virtual-group`.
The virtual groups gidNumber is equal to the uidNumber of the user.

**Additionally**, for both users and (non-virtual) groups, any attributes you set are also present as LDAP Attributes.

:::info
Starting with 2021.9.1, custom attributes will override the inbuilt attributes.
:::

:::info
Starting with 2023.3, periods and slashes in custom attributes will be sanitized.
:::

## SSL / StartTLS

You can also configure SSL for your LDAP Providers by selecting a certificate and a server name in the provider settings.

Starting with authentik 2023.6, StartTLS is supported, and the provider will pick the correct certificate based on the configured _TLS Server name_ field. The certificate is not picked based on the Bind DN, as the StartTLS operation should happen be the bind request to ensure bind credentials are transmitted over TLS.

This enables you to bind on port 636 using LDAPS.

## Integrations

See the integration guide for [sssd](../../../integrations/services/sssd/) for an example guide.

## Bind Modes

All bind modes rely on flows.

The following stages are supported:

-   [Identification](../../flow/stages/identification/index.md)
-   [Password](../../flow/stages/password/index.md)
-   [Authenticator validation](../../flow/stages/authenticator_validate/index.md)

    Note: Authenticator validation currently only supports DUO, TOTP and static authenticators.

    Starting with authentik 2023.6, code-based authenticators are only supported when _Code-based MFA Support_ is enabled in the provider. When enabled, all users that will bind to the LDAP provider should have a TOTP device configured, as otherwise a password might be incorrectly rejected when semicolons are used in the password.

    For code-based authenticators, the code must be given as part of the bind password, separated by a semicolon. For example for the password `example-password` and the code `123456`, the input must be `example-password;123456`.

    SMS-based authenticators are not supported as they require a code to be sent from authentik, which is not possible during the bind.

-   [User Logout](../../flow/stages/user_logout.md)
-   [User Login](../../flow/stages/user_login/index.md)
-   [Deny](../../flow/stages/deny.md)

#### Direct bind

In this mode, the outpost will always execute the configured flow when a new bind request is received.

#### Cached bind

This mode uses the same logic as direct bind, however the result is cached for the entered credentials, and saved in memory for the standard session duration. Sessions are saved independently, meaning that revoking sessions does _not_ remove them from the outpost, and neither will changing a users credentials.

## Search Modes

#### Direct search

Every LDAP search request will trigger one or more requests to the authentik core API. This will always return the latest data, however also has a performance hit due all the layers the backend requests have to go through, etc.

#### Cached search

In this mode, the outpost will periodically fetch all users and groups from the backend, hold them in memory, and respond to search queries directly. This means greatly improved performance but potentially returning old/invalid data.
