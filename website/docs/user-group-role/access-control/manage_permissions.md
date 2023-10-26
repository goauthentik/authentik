---
title: "Manage permissions"
description: "Learn how to use global and object permissions in authentik."
---

Refer to the following topics for instructions to view and manage permissions.

## View permissions

You can view all permissions that are assigned to a user, group, role, flow, or stage.

### View user, group, and role permissions

To view _object_ permissions for a specific user, role, or group:

1. Go to the Admin interface and navigate to **Directory**.
2. Select either **Users**, **Groups**, or **Roles**
3. Select a specific user/group/role by clicking on the name (this opens the details page).
4. Click the **Assigned Permissions** tab at the top of the page (to the right of the **Permissions** tab).
5. Scroll down to see both the global and object-level permissions.

:::info
Note that groups do not have global permissions.
:::

### View flow permissions

1. Go to the Admin interface and navigate to **Flows and Stages -> Flows**.
2. Click the name of the flow (this opens the details page).
3. Click the **Permissions** tab at the top of the page.
4. View the assigned permissions using the **User Object Permissions** and the **Role Object Permissions** tabs.

### View stage permissions

1. Go to the Admin interface and navigate to **Flows and Stages -> Stagess**.
2. On the row for the specific stage whose permissions you want to view, click the lock icon.
3. On the **Update Permissions** tab, you can view the assigned permissions using the **User Object Permissions** and the **Role Object Permissions** tabs.

## Manage permissions

You can assign or remove permissions to a user, role, group, flow, or stage.

### Assign, modify, or remove permissions for a user

To assign or remove _object_ permissions for a specific user:

1. Go to the Admin interface and navigate to **Directory -> Users**.
2. Select a specific user by clicking on the user's name.
3. Click the **Permissions** tab at the top of the page.
4. To assign or remove permissions that another _user_ has on this specific user:
    1. Click the **User Object Permissions** tab, click **Assign to new user**.
    2. In the **User** drop-down, select the user object.
    3. Use the toggles to set which permissions on that selected user object you want to grant to (or remove from) the specific user.
    4. Click **Assign** to save your settings and close the modal.
5. To assign or remove permissions that another _role_ has on this specific user:
    Click the **Role Object Permissions** tab, click **Assign to new role**.
    2. In the **User** drop-down, select the user object.
    3. Use the toggles to set which permissions you want to grant to (or remove from) the selected role.
    4. Click **Assign** to save your settings and close the modal.

To assign or remove _global_ permissions for a user:

1. Go to the Admin interface and navigate to **Directory -> Users**.
2. Select a specific user the clicking on the user's name.
3. Click the **Assigned Permissions** tab at the top of the page (to the right of the **Permissions** tab).
4. In the **Assigned Global Permissions** area, click **Assign Permission**.
5. In the **Assign permissions to user** modal, click the plus sign (**+**) and then click the checkbox beside each permission that you want to assign to the user. To remove permissions, deselct the checkbox.
6. Click **Add**, and then click **Assign** to save your changes and close the modal.

### Assign or remove permissions on a specific group

:::info
Note that groups themselves do not have permissions. Rather, users and roles have permissions assigned that allow them to create, modify, delete, etc., a group.
Also there are no global permissions for groups.
:::

To assign or remove _object_ permissions on a specific group by users and roles:

1. Go to the Admin interface and navigate to **Directory -> Groups**.
2. Select a specific group by clicking the the group's name.
3. Click the **Permissions** tab at the top of the page.
 To assign or remove permissions that another _user_ has on this specific group:
    1. Click the **User Object Permissions** tab, click **Assign to new user**.
    2. In the **User** drop-down, select the user object.
    3. Use the toggles to set which permissions on that selected group you want to grant to (or remove from) the specific user.
    4. Click **Assign** to save your settings and close the modal.
5. To assign or remove permissions that another _role_ has on this specific group:
    Click the **Role Object Permissions** tab, click **Assign to new role**.
    2. In the **Role** drop-down, select the role.
    3. Use the toggles to set which permissions you want to grant to (or remove from ) the selected role.
    4. Click **Assign** to save your settings and close the modal.

### Assign or remove permissions for a specific role

To assign or remove _object_ permissions for a specific role:

1. Go to the Admin interface and navigate to **Directory -> Roles**.
2. Select a specific role the clicking on the role's name.
3. Click the **Permissions** tab at the top of the page.
To assign or remove permissions that another _user_ has on this specific role:
    1. Click the **User Object Permissions** tab, click **Assign to new user**.
    2. In the **User** drop-down, select the user object.
    3. Use the toggles to set which permissions on that role you want to grant to (or remove from) the selected user.
    4. Click **Assign** to save your settings and close the modal.
5. To assign or remove permissions that another _role_ has on this specific group:
    Click the **Role Object Permissions** tab, click **Assign to new role**.
    2. In the **Role** drop-down, select the role.
    3. Use the toggles to set which permissions you want to grant to (or remove from) the selected role.
    4. Click **Assign** to save your settings and close the modal.

To assign or remove _global_ permissions for a role:

1. Go to the Admin interface and navigate to **Directory -> Roles**.
2. Select a specific role by clicking on the role's name.
3. The **Overview** tab at the top of the page displays all assigned global permissions for the role.
4. In the **Assigned Global Permissions** area, click **Assign Permission**.
5. In the **Assign permissions to role** modal, click the plus sign (**+**) and then click the checkbox beside each permission that you want to assign to the role. To remove permissions, deselect the checkbox.
6. Click **Assign** to save your changes and close the modal.

### Assign or remove flow permissions

1. Go to the Admin interface and navigate to **Flows and Stages -> Flows**.
2. Click the name of the flow (this opens the details page).
3. Click the **Permissions** tab at the top of the page.
4. Add or remove permissions using the **User Object Permissions** and the **Role Object Permissions** tabs.

### Assign or remove stage permissions

1. Go to the Admin interface and navigate to **Flows and Stages -> Stagess**.
2. On the row for the specific stage that you want to manage permissions, click the lock icon.
3. On the **Update Permissions** tab, you can add or remove the assigned permissions using the **User Object Permissions** and the **Role Object Permissions** tabs.
