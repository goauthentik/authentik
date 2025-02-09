---
title: Microsoft Entra ID provider
---

<span class="badge badge--primary">Enterprise</span>

---

With the Microsoft Entra ID provider, authentik serves as the single source of truth for all users and groups. Configuring Entra ID as a provider allows for auto-discovery of user and group accounts, on-going synchronization of user data such as email address, name, and status, and integrated data mapping of field names and values.

- For instructions to configure your Entra ID tenant to integrate with authentik, refer to [Configure Entra ID](./setup-entra.md).
- For instructions to add Entra ID as a provider in authentik, refer to [Create a Entra ID provider](./add-entra-provider.md).

## About using Entra ID with authentik

The following sections discuss how Entra ID operates with authentik.

### Discovery

When first creating and configuring the provider, authentik will run a discovery process and query your Entra ID for all users and groups, and attempt to match them with their respective counterparts in authentik. This discovery takes into consideration any **User filtering** options configured in the provider, such as only linking to authentik users in a specific group or excluding service accounts.

This discovery happens every time before a full sync is started.

### Synchronization

There are two types of synchronization: a direct sync and a full sync.

A _direct sync_ happens when a user or group is created, updated or deleted in authentik, or when a user is added to or removed from a group. When one of these events happens, the direct sync automatically forwards those changes to Entra ID.

The _full sync_ happens when the provider is initially created and when it is saved. The full sync goes through all users and groups matching the **User filtering** options set and will create/update them in Entra ID. After the initial sync, authentik will run a full sync every four hours to ensure the consistency of users and groups.

During either sync, if a user or group was created in authentik and a matching user/group exists in Entra ID, authentik will automatically link them together. Furthermore, users present in authentik but not in Entra ID will be created and and linked.

When a property mapping has an invalid expression, it will cause the sync to stop to prevent errors from being spammed. To handle any kind of network interruptions, authentik will detect transient request failures and retry any sync tasks.

### Customization for data mapping

There are a couple of considerations in regard to how authentik data is mapped to Entra ID user/group data by default.

- For users, authentik only saves the full display name, not separate first and family names.
- By default, authentik synchs a user’s email, a user’s name, and their active status between Entra ID and authentik. For groups, the name is synced.

Refer to Microsoft documentation for further details.

- https://learn.microsoft.com/en-us/graph/api/user-post-users?view=graph-rest-1.0&tabs=http#request-body
- https://learn.microsoft.com/en-us/graph/api/group-post-groups?view=graph-rest-1.0&tabs=http#request-body
