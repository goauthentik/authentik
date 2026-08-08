---
title: Internal users
sidebar_label: Internal users
sidebar_position: 1
---

Internal users are accounts for people who need access to authentik's full user experience.

An internal user account can access the authentik application dashboard, open the user settings menu through the authentik user interface, and authenticate to multiple applications from the application dashboard.

For an overview of all account types, see [Account types](./).

For information on creating and managing internal users, see [Managing users](../user_basic_operations.md).

## Application dashboard

After logging in, internal users are redirected to the application dashboard. They can also access the application dashboard directly at:

```text
https://authentik.company/if/user/
```

The application dashboard displays the applications available to the user. Users can select an application to authenticate and continue to it. This makes it easy for an internal user to authenticate to multiple applications without starting each authentication process from a separate application link.

## Access user settings

Unlike [external users](./external-users.md), internal users do not need to be directed to the settings page through a separate link. They can navigate to it from the application dashboard.

Internal users can also acess the user settings page directly at:

```text
https://authentik.company/if/user/#/settings
```

## When to use internal users

Use an internal user account for:

- People who need the full authentik user experience.
- Users who need access to the application dashboard.
- Users who need to access user settings through the authentik user interface.
- Administrators and other users who need to manage authentik, subject to their permissions.

Use an [external user](./external-users.md) when the user should typically authenticate to a single application and should not have access to the application dashboard.
