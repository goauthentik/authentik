---
title: External users
sidebar_label: External users
sidebar_position: 2
---

External users are accounts for people who need access to an application but not to the authentik application dashboard.

Unlike [internal users](./internal-users.md), external users typically authenticate to a single default application.

External users cannot access the application dashboard. They therefore do not have access to the user settings page via the user interface. They can however access the user settings page through a direct URL.

For an overview of all account types, see [Account types](./index.mdx).

For information on creating and managing external users, see [Managing users](../user_basic_operations.md).

## Application access

External users typically authenticate to a single default application. After successful authentication, authentik redirects them to the application configured for the authentication request or to the brand's default application.

Configure a default application for [brands](../../../customize/branding/index.md#external-user-settings) used by external users. Without a default application, an external user who authenticates without requesting a specific application cannot continue to an application.

## Access user settings

External users cannot access the user settings menu through the application dashboard because they do not have access to the dashboard.

To allow an external user to access their settings, direct them to the user settings URL:

```text
https://authentik.company/if/user/#/settings
```

## When to use external users

Use an external user account for:

- Customers or other users in a B2C deployment.
- External consultants, contractors, or volunteers.
- Users who need access to a single application.
- Users who should not see the application dashboard or other available applications.

Use an [internal user](./internal-users.md) when the user needs to access the application dashboard, launch multiple applications, or access their user settings from the application dashboard.
