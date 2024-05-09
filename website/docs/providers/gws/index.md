---
title: Google Workspace provider
---

With the Google Workspace provider, authentik can be the single source of truth for all users and groups, even when using Google products like Gmail.

For instructions to configure your Google Workspace to integrate with authentik, refer to [Configure Google Workspace](./setup-gws).

For instructions to add Google Workspce as a provider, refer to [Create a Google Workspace provider](./add-gws-provider).

## About using Google Workspace with authentik

The following sections discuss how Google Workspace operates with authentik.

### Discovery

When first creating the provider and setting it up correctly, the provider will run a discovery and query your google workspace for all users and groups, and attempt to match them with their respective counterparts in authentik. This matching is done by email address for users as google uses that as their primary identifier, and using group names for groups. This discovery also takes into consideration any **User filtering** options configured in the provider, such as only linking to authentik users in a specific group or excluding service accounts.

This discovery happens every time the provider is saved (**_this might change later to a separate action_**)

### Syncing

There are two types of sync; a direct sync and a full sync.

The full sync happens when the provider is initially created and when it is saved. The full sync goes through all users and groups matching the **User filtering** options set and will create/update them in Google Workspace. In addition to that, the full sync is also run on a schedule every 4 hours.

The direct sync happens when a user/group is created/updated/deleted in authentik, or a member is added/removed to/from a group. The direct sync will only forward those changes to Google Workspace

During either sync, if a user/group was created in authentik and a matching user/group exists in Google Workspace, authentik will link them together as the discovery would do above.

If the user has been deleted in google workspace outside of authentik, authentik will notice this and re-create and re-link the user

When a property mapping has an invalid expression, it will cause the sync to stop to prevent errors from being spammed.

To handle any kind of network interruptions, authentik will detect transient request failures and retry any sync tasks.

### Customization for data mapping

There are a couple of considerations in regard to how authentik data is mapped to google workspace user/group data by default.

*   For users, authentik only saves the full display name, while Google requires given/family name separately, and as such authentik tries to separate the full name automatically with the default User property mapping.

*   For groups, Google groups require an email address. Thus in authentik the provider configuration has an option **Default group email domain**, which will be used in conjunction with the group’s name to generate an email address. This can be customized with a property mapping.

*   By default, authentik maps a user’s email, a user’s name, and their active status. For groups, the name is synced.

Refer to Google documentation for further details:

-   https://developers.google.com/admin-sdk/directory/reference/rest/v1/users#User
-   https://developers.google.com/admin-sdk/directory/reference/rest/v1/groups#Group

