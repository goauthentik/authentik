---
title: Managing flow context keys
---

[Flow context](../../../add-secure-apps/flows-stages/flow/context/index.mdx) can be managed in [Expression policies](../expression.mdx) via the `context['flow_plan'].context` variable.

Here's an example of setting a key in an Expression policy:

```python
context['flow_plan'].context['redirect_stage_target'] = 'ak-flow://redirected-authentication-flow'
```

And here's an example of removing that key:

```python
context['flow_plan'].context.pop('redirect_stage_target', None)
```
