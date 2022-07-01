---
title: Example policy snippets for flows
---

### Redirect current flow to another URL

:::info
Requires authentik 2022.7
:::

```python
plan = request.context["flow_plan"]
plan.redirect("https://foo.bar")
return False
```

This policy should be bound to the stage after your redirect should happen. For example, if you have an identification and a password stage, and you want to redirect after identification, bind the policy to the password stage. Make sure the policy binding is set to re-evaluate policies.
