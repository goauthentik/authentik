---
title: Permissions
description: "Learn how to use global and object permissions in authentik."
---

Permissions are the central nuggets in all acess control systems. Permissions are the lowest-level component, the controlling piece of data, that is assigned (or not assigned or removed!) to users and and roles to define exactly WHO can do WHAT to WHICH component or part of the overall software system.

## Fundamentals of authentik permissions

In authentik, you can assign permissions to either [roles](../roles/index.mdx) (most common and best practice) or to individual [users](../user/index.mdx) (on an as-needed basis).

There are [**_global permissions**_](#global-permissions) and [**_object permissions_**](#object-permissions).

*   **global permissions** define who can do what on a global level, across the entire system. Some examples in authentik are the ability to add a new [flow](../../flow/index.md) or to create a URL for a user to recover their login credentials.

*   **object permissions** are about a specific object (a user, a flow, a stage...), and have two categories:

    *   **user object roles**: defnes WHO can chnage the **_object_**
    *   **role object permissions**: defines which ROLE can change the **_object_**

## View permissions

words here about the various tabs and ways to see who and what has which permissions

## Manage permissions

Permissions are assigned to either a user, role, or group.

*   Assign permissions to a user
*   Assign Permissions to a role
*   Assign permissions to a group


