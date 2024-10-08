---
title: "Manage roles"
description: "Learn how to work with roles and permissions in authentik."
---

Roles are a collection of permissions, which can then be assigned, en masse, to a group. Using roles is a way to quickly grant permissions; by adding a user to the group with the appropriate assigned roles, any user in that group then inherits all of those permissions that are assigned to the role.

:::info
In authentik, we assign roles to groups, not to individual users.
:::

## Create a role

To create a new role, follow these steps:

1. In the Admin interface, navigate to **Directory > Roles**.
2. Click **Create**, enter the name of the role, and then click **Create** in the modal.
3. Next, [assign permissions to the role](../access-control/manage_permissions.md#assign-or-remove-permissions-for-a-specific-role).

## Modify a role

To modify a role, follow these steps:

-   To edit the name of the role, click the Edit icon beside the role's name.

-   To modify the permissions that are assigned to the role click on the role's name to go to the role's detail page. There you can add, modify, or remove permissions. For more information, refer to ["Assign or remove permissions for a specific role"](../access-control/manage_permissions.md#assign-or-remove-permissions-for-a-specific-role).

## Delete a role

To delete a role, follow these steps:

1. In the Admin interface, navigate to **Directory > Roles**.
2. Select the checkbox beside the name of the role that you want to delete.
3. Click **Delete**.

## Assign a role to a group

In authentik, roles are assigned to [groups](../groups/index.mdx), not to individual users.

1.  To assign the role to a group, navigate to **Directory -> Groups**.
2.  Click the name of the group to which you want to add a role.
3.  On the group's detail page, on the Overview tab, click **Edit** in the **Group Info** area.
4.  On the **Update Group** modal, in the **Roles** field, scroll through the list of existent roles, and click to select the one you want to add to the group. (You can select multiple roles at once by holding the Control and Command keys while selecting the roles.)
5.  Click **Update** to add the role(s) and close the modal.

:::info
To remove a role from a group, hold the Command key and click the name of the role that you want to remove from the group. This desepcts the role. Then click **Update**.
:::
