---
title: Google Workspace provider
authentik_enterprise: true
---

The Google Workspace provider allows you to integrate with your Google Workspace organization. It supports syncing users and groups from authentik to Google Workspace, allowing authentik to act as a source of truth for all users and groups.

- For instructions on configuring your Google Workspace organization in prepation for creating a Google Workspace provider, refer to the [Configure Google Workspace](./configure-gws.md) documentation.
- For instructions on creating a Google Workspace provider, refer to the [Create a Google Workspace provider](./create-gws-provider.md) documentation.

## Discovery

Upon creating the Google Workspace provider, it will run a discovery task to query your google workspace for all users and groups, and attempt to match them with their respective counterparts in authentik.

Users are matched on their email address. Groups are matched based on their names.

This discovery also takes into consideration any **User filtering** options configured in the provider, such as only linking to authentik users in a specific group or excluding service accounts. This discovery process occurs each time a full sync is initiated.

## Synchronization

There are two types of synchronization: direct sync and full sync.

### Direct sync

A direct sync occurs when a user or group is created, updated or deleted in authentik, or when a user is added to or removed from a group. When any of these events occur, the direct sync automatically syncs those changes to Google Workspace.

### Full sync

A full sync occurs when the provider is initially created and when it is saved. During a full sync, all users and groups that match the **User filtering** settings are processed and created or updated in Google Workspace. After the initial sync, authentik automatically performs a full sync every four hours to maintain consistency between users and groups.

During the full sync, if a user or group exists in both authentik and Google Workspace, authentik will automatically link them.

Additionally, any users or groups present in authentik but absent in Google Workspace will be created and linked.

## Error handling

When a property mapping has an invalid expression, it will cause a sync to stop to prevent excessive error messages.

To handle network interruptions, authentik detects transient request failures and retries sync tasks.

## Property mapping

There are several considerations regarding how authentik data is mapped to Google Workspace user and group data.

### Users

For users, authentik only saves the full display name, while Google requires given/family name separately, and as such authentik attempts to separate the full name automatically with the `authentik default Google Workspace Mapping: User` property mapping.

By default, authentik maps a user’s: email address, name, and active status.

Refer to Google documentation for further details on which attributes can be mapped: [Google Workspace Reference - Resource: User](https://developers.google.com/admin-sdk/directory/reference/rest/v1/users#User)

### Groups

For groups, Google Workspace groups require an email address. Therefore the Google Workspace provider has an **Default group email domain** setting, which will be used in conjunction with the group’s name to generate an email address. This can be customized with a property mapping.

By default, authentik only maps a group's name.

Refer to Google documentation for further details on which attributes can be mapped: [Google Workspace Reference - Resource: Group](https://developers.google.com/admin-sdk/directory/reference/rest/v1/groups#Group)
