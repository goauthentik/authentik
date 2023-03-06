---
title: SCIM Provider
---

SCIM (System for Cross-domain Identity Management) is a set of APIs to provision users and groups. The SCIM provider in authentik supports SCIM 2.0 and can be used to provision and sync users from authentik into other applications.

:::info
The SCIM provider is currently in Preview.
:::

### Configuration

A SCIM provider requires a base URL and a token. SCIM works via HTTP requests, so authentik must be able to reach the specified endpoint.

When configuring SCIM, you'll get an endpoint and a token from the application that accepts SCIM data. This endpoint usually ends in `/v2`, which corresponds to the SCIM version supported.

The token given by the application will be sent with all outgoing SCIM requests to authenticate them.

### Syncing

Data is synchronized in multiple ways:

-   When a user/group is created/modified/deleted, that action is sent to all SCIM providers
-   Periodically (once an hour), all SCIM providers are fully synchronized

The actual synchronization process is run in the authentik worker. To allow this process to better to scale, a task is started for each 100 users and groups, so when multiple workers are available the workload will be distributed.

### Supported features

SCIM defines multiple optional features, some of which are supported by the SCIM provider.

-   Bulk updates
-   Password changes
-   Etag

### Attribute mapping

Attribute mapping from authentik to SCIM users is done via property mappings as with other providers. The default mappings for users and groups make some assumptions that should work for most setups, but it is also possible to define custom mappings to add fields.

All selected mappings are applied in the order of their name, and are deeply merged onto the final user data. The final data is then validated against the SCIM schema, and if the data is not valid, the sync is stopped.
