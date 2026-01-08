---
title: Microsoft Entra ID provider
authentik_enterprise: true
---

The Entra ID provider allows you to integrate with your Entra ID tenant. It supports syncing users and groups from authentik to Entra ID, allowing authentik to act as a source of truth for all users and groups.

- For instructions on configuring your Entra ID tenant in prepation for creating an Entra ID provider, refer to [Configure Entra ID](./configure-entra.md).
- For instructions on creating an Entra ID provider, refer to [Create an Entra ID provider](./create-entra-provider.md).

## Discovery

Upon creating the Entra ID provider, it will run a discovery task to query your Entra ID tenant for all users and groups, and attempt to match them with their respective counterparts in authentik.

Users are matched on their email address. Groups are matched based on their names.

This discovery also takes into consideration any **User filtering** options configured in the provider, such as only linking to authentik users in a specific group or excluding service accounts. This discovery process occurs each time a [full sync](#full-sync) is initiated.

## Synchronization

There are two types of synchronization: direct sync and full sync.

### Direct sync

A direct sync occurs when a user or group is created, updated or deleted in authentik, or when a user is added to or removed from a group. When any of these events occur, the direct sync automatically syncs those changes to Entra ID.

### Full sync

A full sync occurs when the provider is initially created and when it is saved. During a full sync, all users and groups that match the **User filtering** settings are processed and created or updated in Entra ID. After the initial sync, authentik automatically performs a full sync every four hours by default to maintain consistency between users and groups.

During the full sync, if a user or group exists in both authentik and Entra ID, authentik will automatically link them.

Additionally, any users or groups present in authentik but absent in Entra ID will be created and linked.

## Error handling

When a property mapping has an invalid expression, it will cause a sync to stop to prevent excessive error messages.

To handle network interruptions, authentik detects transient request failures and retries sync tasks.

## Property mapping

There are several considerations regarding how authentik data is mapped to Entra ID user and group data.

### Users

For users, authentik only saves the full display name, not separate first and family names.

By default, authentik maps a user's email address, name, and whether the user is active.

Refer to the Entra ID documentation for further details on which attributes can be mapped: [Microsoft Graph - Create User](https://learn.microsoft.com/en-us/graph/api/user-post-users?view=graph-rest-1.0&tabs=http#request-body)

### Groups

By default, authentik only maps a group's name, `mail_enabled` status, `security_enabled` status and `mail_nickname` (equivalent to name).

Refer to the Entra ID documentation for further details on these attributes and which attributes can be mapped: [Microsoft Graph - Create Group](https://learn.microsoft.com/en-us/graph/api/group-post-groups?view=graph-rest-1.0&tabs=http#request-body)
