---
title: Identification stage
---

This stage provides a ready-to-go form for users to identify themselves.

## User Fields

Select which fields the user can use to identify themselves. Multiple fields can be selected. If no fields are selected, only sources will be shown.

-   Username
-   Email
-   UPN

    UPN will attempt to identify the user based on the `upn` attribute, which can be imported with an [LDAP Source](/integrations/sources/ldap/index)

:::info
Starting with authentik 2023.5, when no user fields are selected and only one source is selected, authentik will automatically redirect the user to that source.
:::

## Password stage

To prompt users for their password on the same step as identifying themselves, a password stage can be selected here. If a password stage is selected in the Identification stage, the password stage should not be bound to the flow.

## Enrollment/Recovery Flow

These fields specify if and which flows are linked on the form. The enrollment flow is linked as `Need an account? Sign up.`, and the recovery flow is linked as `Forgot username or password?`.
