---
title: Ensure unique email addresses
tags:
    - policy
    - expression
    - email
---

By default, authentik does not require email addresses to be unique. If you want to enforce uniqueness, use an [expression policy](./index.mdx) during enrollment or profile-edit flows.

Bind the policy before the [User write stage](../../../../add-secure-apps/flows-stages/stages/user_write.md), or attach it directly to the [Prompt stage](../../../../add-secure-apps/flows-stages/stages/prompt/index.md) that collects the email address.

## Example expression

In this example, `email` must match the field key from your prompt stage. The `pending_user` exclusion lets the same policy work for updates as well as new users.

```python
# Ensure this matches the *Field Key* value of the prompt
field_name = "email"
email = request.context["prompt_data"][field_name]
pending_user = request.context.get("pending_user")

from authentik.core.models import User
query = User.objects.filter(email__iexact=email)
if pending_user:
    query = query.exclude(pk=pending_user.pk)
elif request.user and request.user.is_authenticated:
    query = query.exclude(pk=request.user.pk)

if query.exists():
    ak_message("Email address in use")
    return False

return True
```
