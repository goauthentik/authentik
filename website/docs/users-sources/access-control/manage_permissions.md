---
title: "Manage permissions"
description: "Learn how to use global and object permissions in authentik."
---

For instructions on viewing and managing permissions, see the following topics. To learn more about the concepts and fundamentals of authentik permissions, refer to [About Permissions](./permissions.md).

To learn about using Initial Permissions, a pre-defined set of permissions, refer to our [documentation](./initial_permissions.mdx).

## View permissions

You can view all permissions that are assigned to a user, group, role, flow, stage, or other objects.

### View permissions assigned for a specific role

To view permissions assigned for a specific role:

1. Go to the Admin interface and navigate to **Directory > Roles**
2. Select a specific role by clicking on the name (this opens the details page).
3. Click the **Permissions** tab at the top of the page
4. Select the **Assigned global permissions** sub-tab to see global permissions and the **Assigned object permissions** sub-tab to see the object permissions.

### View permissions on objects with a detail page

Here we'll use flows as an example for objects with a detail page.

1. Go to the Admin interface and navigate to **Flows and Stages > Flows**.
2. Click the name of the flow (this opens the details page).
3. View the assigned permissions by clicking the **Permissions** tab at the top of the page.
4. (Optionally) Hover over any checkmark to see whether that permission is granted by a global permission or an object permission.

### View permissions for objects without a detail page

Here we'll use stages as an example for objects without a detail page.

1. Go to the Admin interface and navigate to **Flows and Stages > Stages**.
2. On the row for the specific stage whose permissions you want to view, click the **lock icon**.
3. View the assigned permissions on the **Update Permissions** window
4. (Optionally) Hover over any checkmark to see whether that permission is granted by a global permission or an object permission.

## Manage permissions

You can assign or remove permissions to a user, role, group, flow, stage, or other objects.

### Assign or remove permissions for a specific role

To assign or remove _object_ permissions for a specific role:

1. Go to the Admin interface and navigate to **Directory > Roles**.
2. Select a specific role by clicking on the role's name.
3. Click the **Permissions** tab at the top of the page, then click the **Role Permissions** tab
4. To assign permissions that another _role_ has on this specific role:
    1. Click **Assign to new role**.
    2. In the **Role** drop-down, select the role object.
    3. Use the toggles to set which permissions on that selected role object you want to grant to the specific role.
    4. Click **Assign** to save your settings and close the box.
5. To remove permissions that another _role_ has on this specific role:
    1. Select the role you'd like to remove object permissions from.
    2. Click **Delete Object Permission**.

To assign or remove _global_ permissions for a role:

1. Go to the Admin interface and navigate to **Directory > Roles**.
2. Select a specific role the clicking on the role's name.
3. Click the **Permissions** tab at the top of the page.
4. Click **Assigned Global Permissions** to the left.
5. To assign permissions that another _role_ has on this specific role: 2. In the **Assign permissions** area, click **Assign Permission**. 3. In the **Assign permission to role** box, click the plus sign (**+**) and then click the checkbox beside each permission that you want to assign to the user. 4. Click **Add**, and then click **Assign** to save your changes and close the box.
6. To remove permissions that another _role_ has on this specific role:
    1. Select the permission(s) you'd like to remove.
    2. Click **Delete Object Permission**.

### Assign `Can view Admin interface` permissions

You can grant regular users, who are not superusers nor Admins, the right to view the Admin interface. This can be useful in scenarios where you have a team who needs to be able to create certain objects (flows, other users, etc) but who should not have full access to the Admin interface.

To assign the `Can view Admin interface` permission to a role:

1. Go to the Admin interface and navigate to **Directory > Role**.
2. Select a specific role the clicking on the role's name.
3. Click the **Permissions** tab at the top of the page.
4. Click **Assigned Global Permissions** to the left.
5. In the **Assign permissions** area, click **Assign Permission**.
6. In the **Assign permission to user** box, click the plus sign (**+**), enter `admin` in the Search field and click the search icon.
7. Select the returned permission, click **Add**, and then click **Assign** to save your changes and close the box.

Be aware that any rights beyond viewing the Admin interface will need to be assigned as well; for example, if you want a non-administrator user to be able to create flows in the Admin interface, you need to grant those global permissions to add flows.
