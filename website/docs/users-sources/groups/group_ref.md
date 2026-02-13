---
title: Group properties and attributes
---

## Object properties

The group object has the following properties:

- `name`: The group's display name.
- `is_superuser`: A boolean field that determines if the group's users are superusers.
- `parents`: The parent groups of this group.
- `roles`: The roles directly assigned to this group.
- `all_roles()`: Returns all roles for this group, including roles inherited from parent groups.
- `attributes`: Dynamic attributes, see [Attributes](#attributes).

## Examples

These are examples of how group objects can be used within authentik policies and property mappings.

### List all group members

Use the following examples to list all users that are members of a group:

```python title="Get all members of a group object"
group.users.all()
```

```python title="Specify a group object based on name and return all of its members"
from authentik.core.models import Group
Group.objects.get(name="name of group").users.all()
```

### List all roles for a group

Use the following examples to list roles assigned to a group:

```python title="Get directly assigned roles for a group object"
group.roles.all()
```

```python title="Get all roles including inherited from parent groups"
group.all_roles()
```

## Attributes

By default, authentik group objects are created with no attributes, however custom attributes can be set.

See [the user reference](../user/user_ref.mdx#attributes) for well-known attributes.
