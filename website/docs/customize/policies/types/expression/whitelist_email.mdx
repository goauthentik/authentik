---
title: Allow only specific email domains
tags:
    - policy
    - expression
    - email
---

Use an [expression policy](./index.mdx) when only specific email domains should be allowed to enroll or authenticate.

The examples below work well with source-related enrollment and authentication flows.

## Restrict enrollment by domain

To update an existing source-enrollment policy:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Open the policy used for source enrollment, such as `default-source-enrollment-if-sso`.
4. Replace the expression body with logic like the example below.
5. Save the policy.

Edit the policy used for source enrollment, such as `default-source-enrollment-if-sso`, and use an expression like this:

```python
allowed_domains = ["example.org", "example.net", "example.com"]

current_domain = request.context["prompt_data"]["email"].split("@")[1] if request.context.get("prompt_data", {}).get("email") else None
if current_domain in allowed_domains:
    email = request.context["prompt_data"]["email"]
    request.context["prompt_data"]["username"] = email
    return ak_is_sso_flow
else:
    ak_message("Enrollment denied for this email domain")
    return False
```

This expression:

- checks the submitted email address
- allows only the domains in `allowed_domains`
- copies the email address into `username` for the rest of the flow
- shows a user-visible error when enrollment is denied

## Restrict authentication by domain

To enforce the same rule for authentication:

1. Log in to authentik as an administrator and open the authentik Admin interface.
2. Navigate to **Customization** > **Policies**.
3. Open the source-authentication policy, such as `default-source-authentication-if-sso`.
4. Update the expression with logic like the example below.
5. Save the policy.

To enforce the same rule during authentication, edit the source-authentication policy, such as `default-source-authentication-if-sso`, and use:

```python
allowed_domains = ["example.org", "example.net", "example.com"]

current_domain = request.user.email.split("@")[1] if hasattr(request.user, 'email') and request.user.email else None
if current_domain in allowed_domains:
    return ak_is_sso_flow
else:
    ak_message("Authentication denied for this email domain")
    return False
```

If you use different flows or policy names, adapt the example to the policy that already governs enrollment or authentication for that source.
