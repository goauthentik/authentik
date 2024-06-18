---
title: Manage groups
description: "Learn how to work with groups in authentik."
---

A group is a collection of users. Refer to the following sections to learn how to create and manage groups, assign users and roles to groups, and how [permissions](../access-control/manage_permissions.md) work on a group level.

## Create a group

To create a new group, follow these steps:

1. In the Admin interface, navigate to **Directory > Groups**.
2. Click **Create** at the top of the Groups page.
3. In the Create modal, define the following:
    - name of the group
    - whether or not users in that group will all be superusers (means anyone in that group has all permissions on everything)
    - the parent group
    - any custom attributes
4. Click **Create**.

## Modify a group

To edit the group's name, parent group, whether or not the group is for superusers, associated roles, and any custom attributes, click the Edit icon beside the role's name. Make the changes, and then click **Update**.

To [add or remove users](../user/user_basic_operations.md#add-a-user-to-a-group) from the group, or to manage permissions assigned to the group, click on the name of the group to go to the group's detail page.

For more information about permissions, refer to ["Assign or remove permissions for a specific group"](../access-control/manage_permissions.md#assign-or-remove-permissions-on-a-specific-group).

## Delete a group

To delete a group, follow these steps:

1. In the Admin interface, navigate to **Directory > Groups**.
2. Select the checkbox beside the name of the group that you want to delete.
3. Click **Delete**.

## Assign a role to a group

You can assign a role to a group, and then all users in the group inherit the permissions assigned to that role. For instructions and more information, see ["Assign a role to a group"](../roles/manage_roles.md#assign-a-role-to-a-group).

## Delegating group member management

:::info
Requires authentik 2024.4
:::

To give a specific Role or User the ability to manage group members, the following permissions need to be granted on the matching Group object:

-   Can view group
-   Can add user to group
-   Can remove user from group
-   Can access admin interface (for managing a group's user within the authentik Admin interface)

In addition, the permission "Can view User" needs to be assigned, either globally or on specific users that should be manageable.

These permissions can be assigned to a [Role](../roles/index.mdx) or directly to a [User](../user/index.mdx).
