---
title: "About permissions"
description: "Learn about global and object permissions in authentik."
---

Permissions are the central components in all access control systems, the lowest-level components, the controlling pieces of access data. Permissions are assigned to (or removed from!) to define exactly WHO can do WHAT to WHICH part of the overall software system.

:::info
Note that global and object permissions only apply to objects within authentik, and not to who can access certain applications (which are access-controlled using [policies](../../customize/policies/index.md)).
:::

For instructions to add, remove, and manage permissions, refer to [Manage Permissions](./manage_permissions.md).

## Fundamentals of authentik permissions

A [role](../roles/index.md) is a collection of permissions. A user or a group may have any number of roles. A user has a certain permission if they have a role that has that permission, or if they are part of a group (either directly or indirectly) which has a role that has that permission.

- Example 1 (no group): Judith has the role "RADIUS", which has every permission for RADIUS providers and property mappings. Then, Judith has permission to add/view/change/delete RADIUS providers or RADIUS property mappings.
- Example 2 (direct group): Marie is part of the group "Auditors". That group has the role "Event Log manager", which in turn has the permissions "Can view Event", "Can change Event", and "Can delete Event". Then, Marie has permissions to view, change, or delete Events.
- Example 3 (indirect group): Elaine is part of the group "Accounting", which has a parent group "Back office", which has a parent group "Employees". The group "Employees" has the role "Read-only, which has view permissions on all object types. Then, Elaine has the permission to view any object in authentik through indirect membership of the "Employees" group.

:::info
From 2025.12, authentik's access control is fully role-based. Before 2025.12, Admins could assign permissions to individual [users](../user/index.mdx). To mimic this behavior of "User permissions", an Admin can
:::

There are two main types of permissions in authentik:

- [**Global permissions**](#global-permissions)
- [**Object permissions**](#object-permissions)

Additionally, authentik employs _initial permissions_ to streamline the process of granting object-level permissions when an object (user or role) is created. This feature automatically adds permissions for newly created objects to the role that created them. For more details, refer to [Initial permissions](./initial_permissions.mdx).

### Global permissions

Global permissions define coarse-grained access control. For example, a role with a global permission of "Can change Flow" can change any [flow](../../add-secure-apps/flows-stages/flow/index.md). Some permissions only make sense as global permissions, e.g. the permission to add a specific object type or whether a user [`Can view admin interface`](./manage_permissions.md#assign-can-view-admin-interface-permissions).

### Object permissions

An object permission grants permission on a single object (e.g. a [user](../user/index.mdx), a [group](../groups/index.mdx), a [role](../roles/index.md), a [flow](../../add-secure-apps/flows-stages/flow/index.md), etc.) instead of all objects of a specific type. For example, a role with only the object permission to change the Default Authentication flow will not be able to change any other flow.

## Viewing permissions

Many objects in authentik's Admin interface have a Permissions view to double-check which roles have access to that particular object. Those permissions describe what those roles can do TO the object detailed on the page.

For example, the Admin interface UI shown below shows the Role Permissions table for the user named Peter.

![](./user-page.png)

You can see in the **Role Permissions** table that the Admin role and one other role (Read-only) have permissions on Peter (that is, on the user object named Peter). The Admin role has all object permissions on this object, while the Read-only role view permission.

Hover over a checkmark to see whether that permission is granted by a global permission or an object permission.
