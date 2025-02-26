---
title: About roles
---

import DocCardList from "@theme/DocCardList";

Roles are a way to simplify the assignment of permissions. Roles are also the backbone of role-based access control (RBAC), an industry standard for managing [access control](../access-control/index.mdx). In authentik, RBAC is how you manage access to system components and specific objects such as flows, stages, users, etc.

Think of roles as a collection of permissions. A role, along with its "bucket" of assigned permissions, can then be assigned to a group, which means that every user who is a part of that group will inherit all of the permissions in that role's "bucket".

For example, let's take a look at the following scenario:

> You need to add 5 new users, all new hires, to authentik, your identity management system. These users will be the first team members on the brand new Security team, so they will need some high-level permissions, with object permissions to create and remove other users, revoke permissions, and send recovery emails. They will also need [global permissions](../access-control/permissions.md#fundamentals-of-authentik-permissions) to control access to flows and stages.

The easiest workflow for setting up these new users involves [creating a role](./manage_roles.md#create-a-role) specifically for their type of work, and then [assigning that role to a group](./manage_roles.md#assign-a-role-to-a-group) to which all of the users belong.

To learn more about working with roles in authentik, refer to the following topics:

<DocCardList />
