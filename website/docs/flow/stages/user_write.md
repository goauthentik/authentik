---
title: User write stage
---

This stages writes data from the current flow context to a user.

Newly created users can be created as inactive and can be assigned to a selected group.

### Dynamic groups

Starting with authentik 2022.5, users can be added to dynamic groups. To do so, simply set `groups` in the flow plan context before this stage is run, for example

```python
from authentik.core.models import Group
group, _ = Group.objects.get_or_create(name="some-group")
# ["groups"] *must* be set to an array of Group objects, names alone are not enough.
request.context["flow_plan"].context["groups"] = [group]
return True
```

### User creation

By default, this stage will create a new user when none is present in the flow context.

Starting with authentik 2022.12, the stage can by default not create new users to prevent users from creating new accounts without authorization.

Starting with authentik 2023.1, this option has been expanded to allow user creation, forbid it or force user creation.
