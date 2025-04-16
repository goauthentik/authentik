---
title: Group properties and attributes
---

## Object properties

The Group object has the following properties:

- `name` Group's display name.
- `is_superuser` Boolean field if the group's users are superusers.
- `parent` The parent Group of this Group.
- `attributes` Dynamic attributes, see [Attributes](#attributes)

## Examples

### List all group members

Use the following examples to list all users that are members of a group:

```python
group.users.all()
```

```python
from authentik.core.models import Group
Group.objects.get(name="name of group").users.all()
```

## Attributes

See [the user reference](../user/user_ref.mdx#attributes) for well-known attributes.
