---
title: Internal users
sidebar_position: 1
---

Internal users are accounts for people who need the authentik application dashboard and their own user settings.

An internal user can sign in to the authentik application dashboard and launch any application available to them. They can also open their user settings from the authentik

For an overview of all account types, see [Account types](./index.mdx). For information on creating and managing internal users, see [Managing users](../user_basic_operations.md).

## Application dashboard

After logging in, internal users are redirected to the application dashboard. They can also access the application dashboard directly at:

```text
https://authentik.company/if/user/
```

The application dashboard displays the applications available to the user. Selecting an application authenticates the user and redirects them to it, so they can reach several applications without a separate link for each one.

## Access user settings

Internal users do not need to be directed to the settings page through a separate link. They can navigate to it from the application dashboard.

Internal users can also access the user settings page directly at:

```text
https://authentik.company/if/user/#/settings
```

## When to use internal users

Use an internal user account for:

- Users who need the full authentik user experience.
- Users who need access to the application dashboard.
- Users who need to access user settings through the authentik user interface.
- Administrators and other users who need to manage authentik, subject to their permissions.

Use an [external user](./external-users.md) when the user typically authenticates to a single application and does not need the application dashboard.
