---
title: External users
sidebar_position: 2
---

External users are accounts for people who need access to an application but not to the authentik application dashboard.

External users cannot access the application dashboard. They therefore do not have access to the user settings page via the user interface. They can however change their password and perform other changes via direct links to the appropriate flow.

For an overview of all account types, see [Account types](./index.mdx).

For information on creating and managing external users, see [Managing users](../user_basic_operations.md).

## Application access

External users typically authenticate to a single default application. After successful authentication, authentik redirects them to the application configured for the authentication request or to the brand's default application.

Configure a default application for [brands](../../../customize/branding/index.md#external-user-settings) used by external users. Without a default application, an external user who signs in without requesting a specific application receives an access-denied page.

## Access user settings

External users cannot access the user settings menu through the application dashboard because they do not have access to the dashboard.

To allow an external user to change their password, enroll an MFA device, or perform other changes that are usually accessed via user settings, you must direct them to the appropriate flow.

## When to use external users

Use an external user account for:

- Customers or other users in a business-to-consumer (B2C) deployment.
- External consultants, contractors, or volunteers.
- Users who need access to a single application.
- Users who should not see the application dashboard or other available applications.

Use an [internal user](./internal-users.md) when someone needs access to the application dashboard to launch multiple applications or manage their user settings from the user interface.
