---
title: Managing flow context keys
tags:
    - policy
    - expression
    - flows
---

[Flow context](../../../../add-secure-apps/flows-stages/flow/context/index.mdx) can be read and updated from an [Expression policy](./index.mdx) through `context["flow_plan"].context`.

This is useful when you want to influence later stages in the same flow, such as changing a redirect target or passing data to another stage.

For `redirect_stage_target`, use the format `ak-flow://{slug}` when you want the [Redirect stage](../../../../add-secure-apps/flows-stages/stages/redirect/index.md) to redirect to another flow. See [`redirect_stage_target`](../../../../add-secure-apps/flows-stages/flow/context/index.mdx#redirect_stage_target-string) for the full behavior.

## Set a flow-context key

```python
context["flow_plan"].context["redirect_stage_target"] = "ak-flow://redirected-authentication-flow"
return True
```

## Remove a flow-context key

```python
context["flow_plan"].context.pop("redirect_stage_target", None)
return True
```

Be careful when modifying flow context in widely reused policies, because the change affects the active flow plan, not only the policy itself.
