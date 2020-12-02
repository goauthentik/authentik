---
title: Prompt stage validation
---

Further validation of prompts can be done using policies.

To validate that two password fields are identical, create the following expression policy:

```python
if request.context.get('prompt_data').get('password') == request.context.get('prompt_data').get('password_repeat'):
    return True

ak_message("Passwords don't match.")
return False
```

This policy expects you to have two password fields with `field_key` set to `password` and `password_repeat`.

Afterwards, bind this policy to the prompt stage you want to validate.
