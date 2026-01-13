---
title: Ensure unique email addresses
---

Due to the database design of authentik, email addresses are by default not required to be unique. However, this behavior can be changed using an expression policy.

The snippet below can be used in an expression policy within enrollment flows. The policy should be bound to any stage before the [User write](../../../add-secure-apps/flows-stages/stages/user_write.md) stage, or with the [Prompt stage](../../../add-secure-apps/flows-stages/stages/prompt/index.md).

```python
# Ensure this matches the *Field Key* value of the prompt
field_name = "email"
email = request.context["prompt_data"][field_name]
pending_user = request.context.get("pending_user")

from authentik.core.models import User
query = User.objects.filter(email__iexact=email)
if pending_user:
    query = query.exclude(pk=pending_user.pk)

if query.exists():
    ak_message("Email address in use")
    return False

return True
```
