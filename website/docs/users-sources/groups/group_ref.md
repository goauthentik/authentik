---
title: Group properties and attributes
---

## Object properties

The Group object has the following properties:

- `name`: The group's display name.
- `is_superuser`: A boolean field that determines if the group's users are superusers.
- `parent`: The parent group of this group.
- `attributes`: Dynamic attributes, see [Attributes](#attributes).

## Examples

These are examples of how group objects can be used within authentik policies and property mappings.

### List all group members

Use the following examples to list all users that are members of a group:

```python title="Get all members of a group object"
group.users.all()
```

```python title="Specify a group object based on name and get all of its members"
from authentik.core.models import Group
Group.objects.get(name="name of group").users.all()
```

## Attributes

By default, authentik Group objects are created with no attributes, however custom attributes can be set.

See [the user reference](../user/user_ref.mdx#attributes) for well-known attributes.
