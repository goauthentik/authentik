---
title: Switch which source is used based on email address
---

You can use an expression policy to determine with [source](../../../../users-sources/sources/) (a set of user credentials and data, stored in authentik, Google, GitHub, etc) is used for a particular user, based on which email address the user enters when they log in and authenticate (using the authn flow).

To switch which source is used for a specific user based on their email domain, [create an expression policy](../working_with_policies.md#create-a-policy) that:

    1. Maps the desired source for each user domain.
    2. Determines the user's domain based on their email address.
    3. Then "switches" the user to the desired source.

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
