---
title: Whitelist email domains
---

To add specific email addresses to an allow list for signing in through SSO or directly with default policy customization,
follow these steps:

1. In the Admin interface, navigate to **Customization > Policies** and modify the default policy named `default-source-enrollment-if-sso`.

2. Add the following code snippet in the policy-specific settings under **Expression** and then click **Update**.

```python
allowed_domains = ["example.net", "example.com"]
current_domain =request.context["prompt_data"]["email"].split("@")[1]
if current_domain in allowed_domains:
  email = request.context["prompt_data"]["email"]
  request.context["prompt_data"]["username"] = email
  return ak_is_sso_flow
else:
  return ak_message("Access denied for this email domain")
```

This configuration specifies the `allowed_domains` list of domains for logging in through SSO, such as Google OAuth2. If your email is not in the available domains, you will receive a 'Permission Denied' message on the login screen.
