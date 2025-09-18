---
title: Switch which source is used based on email address
---

You can use an expression policy to determine with source (a set of user credentials and data, stored in authentik, Google, GitHub, etc) is used for a particular user, based on which email address the user enters when they log in and authenticate (using the authn flow).

To define which source is used, [create an expression policy](../working_with_policies.md#create-a-policy) that defines the possible oiptions for the source, and the logic to determine the domain based on the email address and then "switch" the user to the desired source.

## Example expression

```python
# This is a mapping of domains to sources
# the key is a domain for the user and the value is the `slug` of the source to redirect to
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
