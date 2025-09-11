---
title: User Write stage
---

The User Write stage writes data from the current flow context to a user.

Newly created users can be created as inactive and can be assigned to a selected group.

### Dynamic groups

To add users to dynamic groups, set `groups` in the flow plan context before this stage is run. For example:

```python
from authentik.core.models import Group
group, _ = Group.objects.get_or_create(name="some-group")
# ["groups"] *must* be set to an array of Group objects, names alone are not enough.
request.context["flow_plan"].context["groups"] = [group]
return True
```

### User creation

By default, this stage will create a new user when none is present in the flow context.

To prevent users from creating new accounts without authorization, you can configure the User Write stage to not automatically create new users.

Alternatively, you can configure the stage to explicitly allow user creation, forbid it, or force user creation.
