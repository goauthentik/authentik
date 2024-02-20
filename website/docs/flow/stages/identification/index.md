---
title: Identification stage
---

This stage provides a ready-to-go form for users to identify themselves.

## User Fields

Select which fields the user can use to identify themselves. Multiple fields can be selected. If no fields are selected, only sources will be shown.

-   Username
-   Email
-   UPN

    UPN will attempt to identify the user based on the `upn` attribute, which can be imported with an [LDAP Source](/integrations/sources/ldap/)

## Password stage

To prompt users for their password on the same step as identifying themselves, a password stage can be selected here. If a password stage is selected in the Identification stage, the password stage should not be bound to the flow.

## Enrollment/Recovery Flow

These fields specify if and which flows are linked on the form. The enrollment flow is linked as `Need an account? Sign up.`, and the recovery flow is linked as `Forgot username or password?`.

## Pretend user exists

:::info
Requires authentik 2024.2
:::

When enabled, any user identifier will be accepted as valid (as long as they match the correct format, i.e. when [User fields](#user-fields) is set to only allow Emails, then the identifier still needs to be an Email). The stage will succeed and the flow will continue to the next stage. Stages like the [Password stage](../password/index.md) and [Email stage](../email/index.mdx) are aware of this "pretend" user and will behave the same as if the user would exist.

## Source settings

Some sources (like the [OAuth Source](../../../../integrations/sources/oauth/) and [SAML Source](../../../../integrations/sources/saml/)) require user interaction. To make these sources available to users, they can be selected in the Identification stage settings, which will show them below the selected [user field](#user-fields).

By default, sources are only shown with their icon, which can be changed with the _Show sources' labels_ option.

Furthermore, it is also possible to deselect any [user field option](#user-fields) for an Identification stage, which will result in users only being able to use currently configured sources.

:::info
Starting with authentik 2023.5, when no user fields are selected and only one source is selected, authentik will automatically redirect the user to that source. This only applies when the **Passwordless flow** option is _not_ configured.
:::

## Flow settings

### Passwordless flow

See [Passwordless authentication](../authenticator_validate/index.md#passwordless-authentication).

### Enrollment flow

Optionally can be set to a flow with the designation of _Enrollment_, which will allow users to sign up.

### Recovery flow

Optionally can be set to a flow with the designation of _Recovery_, which will allow users to recover their credentials.
