---
title: User write stage
---

The User Write stage writes data from the current flow context into a user object.

## Overview

This stage updates the current `pending_user`, or creates a new user if the flow does not already have one and the configured creation mode allows it.

It is commonly used in enrollment, recovery, and profile-update flows after a [Prompt stage](../prompt/index.md) has collected input into `prompt_data`.

## Configuration options

- **User creation mode**: control whether the stage never creates users, creates them only when required, or always creates them.
- **Create users as inactive**: mark newly created users inactive.
- **Create users group**: optionally add newly created users to a specific group.
- **User type**: select the user type applied to newly created users.
- **User path template**: optional template used to place newly created users into a path.

## Flow integration

Use this stage after one or more stages that populate flow context, usually a [Prompt stage](../prompt/index.md), [Identification stage](../identification/index.md), or [Email stage](../email/index.md).

In enrollment flows, this stage is often followed by [User Login](../user_login/index.md) so the newly created user is signed in immediately.

## Notes

### Dynamic groups

To add users to dynamic groups, set `groups` in the flow plan context before this stage runs. The value must be a list of actual `Group` objects:

```python
from authentik.core.models import Group

group, _ = Group.objects.get_or_create(name="some-group")
request.context["flow_plan"].context["groups"] = [group]
return True
```
