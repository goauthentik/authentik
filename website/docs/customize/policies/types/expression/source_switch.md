---
title: Switch which source is used based on email address
tags:
    - policy
    - expression
    - sources
---

You can use an [expression policy](./index.mdx) to route users to different [sources](../../../../../users-sources/sources/) based on the email address they enter.

This is useful when different email domains should authenticate against different upstream identity providers.

## Create the policy

[Create an expression policy](../../working_with_policies.md#create-a-policy) that:

1. maps email domains to source slugs
2. reads the identifier collected earlier in the flow
3. redirects the user to the matching source when a mapping exists

## Where to bind it

Bind the expression to the stage binding immediately after the [Identification stage](../../../../add-secure-apps/flows-stages/stages/identification/index.mdx), or after whichever stage first collects the identifier you want to inspect.

For more background on binding policies to stages, see [Working with policies](../../working_with_policies.md#bind-a-policy-to-a-stage-binding).

## Example expression

```python
# Map email domains to source slugs.
source_email_map = {
    "foo.bar.com": "entra-foo",
    "bar.baz.com": "entra-bar",
}

user_email = request.context["pending_user_identifier"]

_username, _, domain = user_email.partition("@")
source = source_email_map.get(domain)
if not source:
    return True

plan = request.context.get("flow_plan")
if not plan:
    return False

# For OIDC
# plan.redirect(f"/source/oauth/login/{source}/")
# For SAML
plan.redirect(f"/source/saml/{source}")
return False
```

## How it works

- The policy reads `pending_user_identifier`, which is the identifier gathered earlier in the flow.
- If the email domain is not in the mapping, the policy returns `True` and flow execution continues normally.
- If the domain maps to a source, the policy redirects the flow and returns `False` so the current path does not continue.

Adjust the redirect path for the source type you use. The example above includes both OIDC and SAML patterns.
