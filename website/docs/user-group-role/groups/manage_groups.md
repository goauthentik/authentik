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

## Assign, modify, or remove permissions for a group

You can grant a group specific global or object-level permissions. Any user who is a member of a group inherits all of the group's permissions.

For more information, review ["Permissions"](../access-control/permissions.md).

## Assign a role to a group

You can assign a role to a group, and then all users in the group inherit the permissions assigned to that role. For instructions and more information, see ["Assign a role to a group"](../roles/manage_roles.md#assign-a-role-to-a-group).
