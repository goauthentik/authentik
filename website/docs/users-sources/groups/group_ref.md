---
title: Group properties and attributes
---

## Object properties

The Group object has the following properties:

- `name`: The group's display name.
- `is_superuser`: A boolean field that determines if the Group's users are superusers.
- `parent`: The parent Group of this Group.
- `attributes`: Dynamic attributes, see [Attributes](#attributes)

## Examples

These are examples of how Group objects can be used within **Policies** and **Property Mappings**.

### List all group members

Use the following examples to list all users that are members of a Group:

```python title="Get all members of a Group object"
group.users.all()
```

```python title="Define a Group object based on name and get all of its members"
from authentik.core.models import Group
Group.objects.get(name="name of group").users.all()
```

## Attributes

By default, authentik Group objects are created with no attributes, however custom attributes can be set.

See [the user reference](../user/user_ref.mdx#attributes) for well-known attributes.
