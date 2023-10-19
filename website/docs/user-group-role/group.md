---
title: About groups
---

## Hierarchy

Groups can be children of another group. Members of children groups are effective members of the parent group.

When you bind a group to an application or flow, any members of any child group of the selected group will have access.

Recursion is limited to 20 levels to prevent deadlocks.

## Attributes

Attributes of groups are recursively merged, for all groups the user is a _direct_ member of.

### Assign, modify, or remove permissions for a group

You can grant a group specific global or object-level permissions. Any user who is a member of a group inherits all of the group's permissions.

For more information, review ["Permissions: global and object-level"](../access-control/permissions.md).
