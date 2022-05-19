---
title: User write stage
---

This stages writes data from the current context to the current pending user. If no user is pending, a new one is created.

Newly created users can be created as inactive and can be assigned to a selected group.

### Dynamic groups

Starting with authentik 2022.5, users can be added to dynamic groups. To do so, simply set `groups` in the flow plan context before this stage is run, for example

```python
from authentik.core.models import Group
group, _ = Group.objects.get_or_create(name="some-group")
# ["groups"] *must* be set to an array of Group objects, names alone are not enough.
request.context["groups"] = [group]
return True
```
