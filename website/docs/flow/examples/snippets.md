---
title: Example policy snippets for flows
---

### Redirect current flow to another URL

:::info
Requires authentik 2022.7
:::

```python
plan = request.context.get("flow_plan")
if not plan:
    return False
plan.redirect("https://foo.bar")
return False
```

This policy should be bound to the stage after your redirect should happen. For example, if you have an identification and a password stage, and you want to redirect after identification, bind the policy to the password stage. Make sure the stage binding's option _Evaluate when stage is run_ is enabled.

### Deny flow when user is authenticated

```python
return not request.user.is_authenticated
```

When used with authentik 2022.7 or later, set the flow _Denied action_ to _CONTINUE_. This will redirect already authenticated users to the default interface if they try to use the respective flow.
