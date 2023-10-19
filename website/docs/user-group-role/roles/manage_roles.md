---
title: "Manage roles"
description: "Learn how to work with roles and permissions in authentik."
---

Roles are a collection of permissions, which can then be assigned, en masse, to a group.

Using roles is a way to quickly grant permissions; by adding a user to the group with the appropriate permissions, that user inherits all of those permissins that are assigned to the group.

:::info
In authentik, we assign roles to groups, not to individual users.
:::

## Create a role

To create a new role, follow these steps:

1. In the Admin interface, navigate to **Directory > Roles**.

2. Click **Create**, and then define the name of the role and click **Create** in the modal.

## Modify a role

To modify a role, follow these steps:

*   To edit the name of the role click the Edit icon beside the role's name.

*   To modify the permissions that are assigned to the role click on the role's name to go to the role's detail page. There you can add, modify, or remove permissions. For more information, refer to ["Assign or remove permissions for a specific role"](../access-control/permissions.md#assign-or-remove-permissions-for-a-specific-role).

## Delete a role

To delete a role, follow these steps:

1. In the Admin interface, navigate to **Directory > Roles**.

2. Select the checkbox beside the name of the role that you want to delete.

3. Click **Delete**.
