---
title: Ensure unique email addresses
---

Due to the database design of authentik, email addresses are by default not required to be unique. This behavior can however be changed by policies.

The snippet below can be used as the expression in policies both with enrollment flows, where the policy should be bound to any stage before the [User write](../../../add-secure-apps/flows-stages/stages/user_write.md) stage, or with the [Prompt stage](../../../add-secure-apps/flows-stages/stages/prompt/index.md).

```python
from authentik.core.models import User

# Ensure this matches the *Field Key* value of the prompt
field_name = "email"
email = request.context["prompt_data"][field_name]
if User.objects.filter(email=email).exists():
  ak_message("Email address in use")
  return False
return True
```
