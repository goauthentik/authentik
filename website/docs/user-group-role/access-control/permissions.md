---
title: "About permissions"
description: "Learn about global and object permissions in authentik."
---

Permissions are the central components in all access control systems, the lowest-level component, the controlling piece of access data. Permissions are assigned to (or removed from!) to define exactly WHO can do WHAT to WHICH part of the overall software system.

## Fundamentals of authentik permissions

There are two main types of permissions in authentik:

-   [**Global permissions**](#global-permissions)
-   [**Object permissions**](#object-permissions)

### Global permissions

Global permissions define who can do what on a global level, across the entire system. Some examples in authentik are the ability to add new [flows](../../flow/index.md) or to create a URL for users to recover their login credentials.

You can assign _global permissions_ to individual [users](../user/index.mdx) or to [roles](../roles/index.mdx) (most common and best practice).

### Object permissions

Object permissions have two categories:

-   **_User_ object permissions**: defines WHO (which user) can change the **_object_**
-   **_Role_ object permissions**: defines which ROLE can change the **_object_**

Object permissions are assigned, as the name indicates, to an object (users, [groups](../groups/index.mdx), roles, flows, and stages), and the assigned permissions state exactly what a user or role can do TO the object (i.e. what permissions does the user or role have on that object).

When working with object permissions, it is important to understand that when you are viewing a page for a specific object (a flow, a stage, user, role, or group), the permissions table on that page displays which users or roles have permissions ON that object, what they can do TO that object that the page is showing.

For example, the UI below shows a user page for the user named Peter.

![](./user-page.png)

You can see in the **User Object Permissions** table that another user, roberto, has permissions on Peter (that is, on the user object Peter).

Looking at another example, with a flow object called `default-recovery-flow` you can see that the Admin user (akadmin) has all object permissions on the flow, but roberto only has a few permissions on that flow.

![](./flow-page.png)
